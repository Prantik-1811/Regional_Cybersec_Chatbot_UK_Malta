"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.
ULTRA-STRICT GROUNDING VERSION
"""

import chromadb
from chromadb.utils import embedding_functions
import os
import re
from dotenv import load_dotenv
load_dotenv()


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

            self.llm = ChatOllama(
                model="llama3.2",
                temperature=0,
                base_url=ollama_base_url,
                num_predict=400,
                stop=["Sources:"]
            )

            self.ChatPromptTemplate = ChatPromptTemplate
            print(f"Connected to Ollama at {ollama_base_url}")

        except Exception as e:
            print(f"Warning: Ollama not available: {e}")


    def query(self, query_text: str, region: str = "UK"):

        if not self.llm:
            return "The local AI engine is not running. Please start Ollama.", []

        # --------------------------------------------------
        # 1️⃣ DEEP RETRIEVAL (Slightly Increased Depth)
        # --------------------------------------------------
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=10  # increased for better candidate pool
            )
        except Exception as e:
            return f"Vector database error: {e}", []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents:
            return "The knowledge base does not contain sufficient information.", []

        # --------------------------------------------------
        # 2️⃣ SMART FILTER (Balanced Strictness)
        # --------------------------------------------------

        query_words = set(re.findall(r"\w+", query_text.lower()))
        candidates = []

        for doc, meta, dist in zip(documents, metadatas, distances):

            if dist is None:
                continue

            # Slightly relaxed similarity threshold
            if dist < 1.2:

                doc_words = set(re.findall(r"\w+", doc.lower()))
                overlap = len(query_words.intersection(doc_words))

                if overlap >= 1:  # was 2 (too strict sometimes)
                    candidates.append((dist, doc, meta))

        if not candidates:
            return "The knowledge base does not contain sufficient information.", []

        candidates.sort(key=lambda x: x[0])

        # --------------------------------------------------
        # 3️⃣ SOURCE DIVERSITY (Same Logic)
        # --------------------------------------------------

        selected_docs = []
        selected_meta = []
        used_urls = set()

        for dist, doc, meta in candidates:

            url = meta.get("source_url", "unknown")

            if url not in used_urls:
                selected_docs.append(doc)
                selected_meta.append(meta)
                used_urls.add(url)

            if len(selected_docs) >= 5:  # increased context depth
                break

        # --------------------------------------------------
        # 4️⃣ CONTROL CONTEXT SIZE
        # --------------------------------------------------

        max_chars = 3500  # increased for richer responses
        context = ""

        for doc in selected_docs:
            if len(context) + len(doc) <= max_chars:
                context += "\n\n" + doc
            else:
                break

        # --------------------------------------------------
        # 5️⃣ SPECIALISED GROUNDING PROMPT
        # --------------------------------------------------

        prompt = self.ChatPromptTemplate.from_template("""
    You are CyberSafe AI, a UK cybersecurity assistant specialising in practical incident guidance.

    Your role is to transform the CONTEXT into a highly specific, grounded response.

    STRICT RULES:

    • Use ONLY information found in the context.
    • Base your answer on concrete details from the articles.
    • Mention specific techniques, examples, or scenarios described.
    • If organisations, procedures, or recommendations are mentioned in the context, include them.
    • Do NOT give generic cybersecurity advice.
    • Do NOT add information that is not explicitly present.
    • Do NOT invent statistics, contacts, or organisations.
    • Write naturally in British English.
    • Where helpful, reference article titles inside the response like:
    (as discussed in "Article Title").

    If the context lacks relevant information, respond exactly:
    "The knowledge base does not contain sufficient information."

    Context:
    {context}

    User Question:
    {question}

    Grounded Response:
    """)

        # --------------------------------------------------
        # 6️⃣ GENERATE
        # --------------------------------------------------

        try:
            chain = prompt | self.llm

            response = chain.invoke({
                "question": query_text,
                "context": context
            })

            answer = response.content.strip()

            # Additional hallucination guard
            if any(word in answer.lower() for word in ["fbi", "us department", "europol", "interpol"]):
                if answer.lower() not in context.lower():
                    return "The knowledge base does not contain sufficient information.", []

        except Exception as e:
            return f"LLM generation error: {e}", []

        # --------------------------------------------------
        # 7️⃣ CLEAN SOURCES
        # --------------------------------------------------

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

        return answer, sources
