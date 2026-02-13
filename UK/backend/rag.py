"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.
Optimised for faster response time and better grounding.

This module handles the core AI logic:
1. Receives a user question.
2. vector searches the database for relevant chunks (Retrieval).
3. Constructs a prompt with the retrieved context.
4. Generates a grounded answer using the local LLM (Generation).
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()


# -------------------------
# RAG Pipeline Class
# -------------------------

class RAGPipeline:
    def __init__(self):
        """
        Initialize vector DB connection and LLM model.
        """
        # 1. Setup ChromaDB
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)

        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Attempt to load existing collection, or create if missing
        try:
            self.collection = self.client.get_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            print(f"Loaded collection with {self.collection.count()} chunks")
        except Exception:
            self.collection = self.client.create_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            print("Created new collection: uk_cyber_knowledge")

        # 2. Setup LLM (Ollama)
        self.llm = None
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate

            # Optimization: Using 'llama3.2' with 'num_predict=300' for faster, concise responses.
            # Temperature 0 ensures the model sticks to facts (less creative hallucinations).
            self.llm = ChatOllama(
                model="llama3.2",
                temperature=0,
                base_url=ollama_base_url,
                num_predict=300
            )

            self.ChatPromptTemplate = ChatPromptTemplate
            print(f"Connected to Ollama at {ollama_base_url}")

        except Exception as e:
            print(f"Warning: Ollama not available: {e}")


    def query(self, query_text: str, region: str = "UK"):
        """
        Execute the full RAG workflow for a query.
        
        Steps:
        1. Search DB for top 3 relevant chunks.
        2. Format context string.
        3. Prompt LLM with context + question.
        4. Return answer and source metadata.
        """

        if not self.llm:
            return (
                "The local AI engine is not running. "
                "Please ensure Ollama is started."
            ), []

        # 1️⃣ Fast Retrieval
        # We limit results to 2 for speed. Quality > Quantity.
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=2
            )
        except Exception as e:
            return f"Vector database error: {e}", []

        # Parse results (Chroma returns lists of lists)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return (
                "I could not find relevant information in the knowledge base. "
                "For official UK guidance, please visit ncsc.gov.uk."
            ), []

        # 2️⃣ Context limiting
        # Truncate total context to 2000 chars to avoid hitting token limits and ensure speed.
        context = "\n\n".join(documents[:2])[:2000]

        # 3️⃣ Strong Grounding Prompt
        # Forces the model to use the context and speak in British English.
        prompt = self.ChatPromptTemplate.from_template("""
You are CyberSafe AI, a UK cybersecurity assistant.

Guidelines:
- Use the provided context to inform your answer.
- If the context is limited, provide general UK cybersecurity guidance.
- Do not invent specific statistics or fake sources.
- Use British English spelling (e.g. 'defence').
- If cybercrime is mentioned, recommend reporting to Action Fraud.

Context:
{context}

User Question:
{question}

Answer:
""")

        # 4️⃣ Generate Response
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "question": query_text,
                "context": context
            })
            answer = response.content.strip()
        except Exception as e:
            return f"LLM generation error: {e}", []

        # 5️⃣ Deduplicate Sources
        # Often multiple chunks come from the same URL, we only want to list it once.
        seen = set()
        sources = []

        for metadata in metadatas:
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

        return answer, sources
