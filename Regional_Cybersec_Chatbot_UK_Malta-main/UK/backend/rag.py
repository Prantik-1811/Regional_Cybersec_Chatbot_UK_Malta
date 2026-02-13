"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.
Optimised for faster response time and better grounding.
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()


# -------------------------
# RAG Pipeline
# -------------------------

class RAGPipeline:
    def __init__(self):
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)

        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

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

        self.llm = None
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate

            # 🔥 Faster model + token limit
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
        """Query the knowledge base and generate a response using RAG."""

        if not self.llm:
            return (
                "The local AI engine is not running. "
                "Please ensure Ollama is started."
            ), []

        # 1️⃣ Faster retrieval (reduced results)
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=2
            )
        except Exception as e:
            return f"Vector database error: {e}", []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return (
                "I could not find relevant information in the knowledge base. "
                "For official UK guidance, please visit ncsc.gov.uk."
            ), []

        # 2️⃣ Limit context size (major speed boost)
        context = "\n\n".join(documents[:2])[:2000]

        # 3️⃣ Stronger grounding prompt
        prompt = self.ChatPromptTemplate.from_template("""
You are CyberSafe AI, a UK cybersecurity assistant.

STRICT RULES:
- Use ONLY the provided context.
- Do NOT invent information.
- Do NOT assume facts not stated.
- If unsure, say you do not have enough information.
- Use British English.
- If cybercrime is mentioned, recommend reporting to Action Fraud.

Context:
{context}

User Question:
{question}

Answer:
""")

        # 4️⃣ Generate response
        try:
            chain = prompt | self.llm
            response = chain.invoke({
                "question": query_text,
                "context": context
            })
            answer = response.content.strip()
        except Exception as e:
            return f"LLM generation error: {e}", []

        # 5️⃣ Clean + deduplicate sources
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
