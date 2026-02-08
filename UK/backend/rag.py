"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.
Uses ChromaDB for vector storage and Ollama for local LLM inference.
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()


class RAGPipeline:
    def __init__(self):
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        # Embedding function (same as ingestion)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            print(f"Loaded collection with {self.collection.count()} documents")
        except Exception:
            self.collection = self.client.create_collection(
                name="uk_cyber_knowledge",
                embedding_function=self.ef
            )
            print("Created new collection: uk_cyber_knowledge")
        
        # Initialize Ollama LLM
        self.llm = None
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate
            
            self.llm = ChatOllama(
                model="llama3.2",
                temperature=0,
                base_url=ollama_base_url
            )
            self.ChatPromptTemplate = ChatPromptTemplate
            print(f"Connected to Ollama at {ollama_base_url}")
        except Exception as e:
            print(f"Warning: Ollama not available: {e}")
    
    def query(self, query_text: str, region: str = "UK"):
        """Query the knowledge base and generate a response."""
        
        # Search for relevant documents
        results = self.collection.query(
            query_texts=[query_text],
            n_results=5,
            where={"region": region} if region else None
        )
        
        if not results['documents'] or not results['documents'][0]:
            return (
                "I can only answer using official UK cybersecurity information. "
                "No relevant data was found. Please run ingest.py first.",
                []
            )
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        # Build context with relevant sources
        RELEVANCE_THRESHOLD = 1.2
        context_parts = []
        sources = []
        
        for i, doc in enumerate(documents):
            distance = distances[i]
            meta = metadatas[i]
            
            if distance < RELEVANCE_THRESHOLD:
                source_num = len(sources) + 1
                title = meta.get('title', 'Unknown')
                context_parts.append(f"[Source {source_num}] {title}\nContent: {doc}")
                sources.append({
                    "title": title,
                    "url": meta.get('source_url', ''),
                    "region": meta.get('region', 'UK')
                })
        
        context = "\n\n".join(context_parts)
        
        if not context:
            return (
                "I can only answer using official UK cybersecurity information. "
                "No relevant data was found.",
                []
            )
        
        # Generate response with LLM
        if self.llm:
            prompt = self.ChatPromptTemplate.from_template("""
                You are a UK cybersecurity expert assistant.
                Answer the user's question strictly based on the provided context from official government sources.
                
                IMPORTANT: Cite sources using [1], [2], etc.
                If the answer is not in the context, say so.
                
                Context:
                {context}
                
                Question: {question}
                
                Answer:
            """)
            
            try:
                chain = prompt | self.llm
                response = chain.invoke({"context": context, "question": query_text})
                answer = response.content
            except Exception as e:
                answer = f"**AI Unavailable**\n\n{context}"
        else:
            answer = f"**Ollama not running**\n\nRelevant information:\n\n{context}"
        
        return answer, sources
