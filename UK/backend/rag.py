"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.
HIGH-PRECISION SPECIALISED VERSION
"""

# Import ChromaDB for vector database operations
# Import embedding function utilities from ChromaDB
# OS module for environment variable handling
# Load environment variables from .env file
# Load environment variables at startup


import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
load_dotenv()


class RAGPipeline:
    def __init__(self):
        # Get persistent database path from environment variable
        # Default to ./chroma_db if not specified
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")

        # Create persistent Chroma client (data stored on disk)
        self.client = chromadb.PersistentClient(path=chroma_path)

        # Use SentenceTransformer model for text embeddings
        # all-MiniLM-L6-v2 is lightweight and efficient for semantic search
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Try loading existing collection
        try:
            self.collection = self.client.get_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            # Print number of stored document chunks
            print(f"Loaded collection with {self.collection.count()} chunks")

        # If collection doesn't exist, create a new one
        except Exception:
            self.collection = self.client.create_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            print("Created new collection: uk_cyber_knowledge")

        # Placeholder for LLM
        self.llm = None

        # Get Ollama base URL from environment
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        # Attempt to connect to Ollama LLM via LangChain
        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate

            # Initialise LLM with deterministic output (temperature=0)
            self.llm = ChatOllama(
                model="llama3.2",
                temperature=0,
                base_url=ollama_base_url,
                num_predict=300  # Max token generation limit
            )

            # Store prompt template class for later use
            self.ChatPromptTemplate = ChatPromptTemplate

            print(f"Connected to Ollama at {ollama_base_url}")

        # If Ollama not running or not installed
        except Exception as e:
            print(f"Warning: Ollama not available: {e}")


    def query(self, query_text: str, region: str = "UK"):
        """Highly specialised and relevance-ranked RAG query."""

        # If LLM not connected, return early
        if not self.llm:
            return (
                "The local AI engine is not running. Please start Ollama."
            ), []

        # --------------------------------------------------
        # 🔹 1. DEEP RETRIEVAL (More candidate chunks)
        # --------------------------------------------------
        # Retrieve top 8 most similar chunks from vector DB
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=8   # Increased retrieval depth
            )
        except Exception as e:
            # Handle database errors safely
            return f"Vector database error: {e}", []

        # Extract documents, metadata and similarity distances
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # If nothing retrieved, return fallback
        if not documents:
            return (
                "The knowledge base does not contain sufficient information."
            ), []

        # --------------------------------------------------
        # 🔹 2. HARD RELEVANCE FILTERING
        # --------------------------------------------------
        # Filter only highly relevant results
        candidates = []

        for doc, meta, dist in zip(documents, metadatas, distances):

            # Skip invalid distance results
            if dist is None:
                continue

            # Strict similarity threshold (lower distance = better match)
            if dist < 1.05:
                candidates.append((dist, doc, meta))

        # If no strong candidates found
        if not candidates:
            return (
                "The knowledge base does not contain sufficient information."
            ), []

        # Sort by strongest semantic similarity
        candidates.sort(key=lambda x: x[0])

        # --------------------------------------------------
        # 🔹 3. SOURCE DIVERSITY (Avoid same article spam)
        # --------------------------------------------------
        # Select top diverse documents (avoid duplicate URLs)
        selected_docs = []
        selected_meta = []
        used_urls = set()

        for dist, doc, meta in candidates:

            # Extract source URL from metadata
            url = meta.get("source_url", "unknown")

            # Prefer different sources unless highly ranked
            if url not in used_urls or len(selected_docs) < 2:
                selected_docs.append(doc)
                selected_meta.append(meta)
                used_urls.add(url)

            # Limit to 4 context chunks
            if len(selected_docs) >= 4:
                break

        # --------------------------------------------------
        # 🔹 4. CONTROLLED CONTEXT WINDOW
        # --------------------------------------------------
        # Limit total context size to prevent token overflow
        max_chars = 3000
        context = ""

        for doc in selected_docs:
            # Add document if within size limit
            if len(context) + len(doc) <= max_chars:
                context += "\n\n" + doc
            else:
                break

        # --------------------------------------------------
        # 🔹 5. SPECIALISED EVIDENCE-BASED PROMPT
        # --------------------------------------------------
        # Create strict, controlled LLM prompt
        prompt = self.ChatPromptTemplate.from_template("""
You are CyberSafe AI, a UK cybersecurity assistant.

STRICT PROFESSIONAL RULES:

• Answer ONLY using information found in the context.
• Extract specific actions, organisations, procedures, or steps when available.
• Prefer concrete guidance over general cybersecurity advice.
• Do NOT generate generic safety recommendations unless clearly stated in context.
• Do NOT invent statistics, URLs, or procedures.
• If multiple steps are present, present them clearly and logically.
• Use British English spelling and tone.

If the answer is NOT clearly supported by the context, respond EXACTLY with:
"The knowledge base does not contain sufficient information."

Context:
{context}

User Question:
{question}

Answer:
""")

        # --------------------------------------------------
        # 🔹 6. GENERATE ANSWER
        # --------------------------------------------------
        # Combine prompt and LLM using LangChain pipeline operator
        try:
            chain = prompt | self.llm

            # Invoke LLM with context and question
            response = chain.invoke({
                "question": query_text,
                "context": context
            })

            # Clean whitespace
            answer = response.content.strip()

        except Exception as e:
            # Handle generation errors safely
            return f"LLM generation error: {e}", []

        # --------------------------------------------------
        # 🔹 7. CLEAN + DEDUP SOURCES
        # --------------------------------------------------
        # Remove duplicate source URLs in final output
        seen = set()
        sources = []

        for metadata in selected_meta:
            if not metadata:
                continue

            url = metadata.get("source_url", "#")

            if url not in seen:
                seen.add(url)
                sources.append({
                    "title": metadata.get("title", "Unknown Source"),
                    "url": url,
                    "type": metadata.get("type", "reference")
                })

        # Return final answer and structured source list
        return answer, sources
