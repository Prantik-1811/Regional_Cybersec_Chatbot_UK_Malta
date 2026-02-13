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
        
        # DIRECT OLLAMA CHAT (No RAG)
        # We are skipping vector search to let the model use its own knowledge.
        
        # Static sources for general reference
        sources = [
            {"url": "https://www.ncsc.gov.uk", "title": "National Cyber Security Centre (NCSC)", "type": "official"},
            {"url": "https://www.actionfraud.police.uk", "title": "Action Fraud", "type": "official"}
        ]
        
        answer = ""
        
        if self.llm:
            prompt = self.ChatPromptTemplate.from_template("""
                You are "CyberSafe AI", a friendly and knowledgeable UK cybersecurity expert assistant.
                
                Your goal is to have a natural, helpful conversation with the user about online safety and cyber threats.
                
                IMPORTANT:
                - Be conversational, empathetic, and clear.
                - Use British English spelling (e.g., 'organisation', 'defence', 'behaviour').
                - You can discuss any cybersecurity topic freely using your own knowledge.
                - If asked about reporting a crime, always recommend Action Fraud.
                - Keep your answers concise and easy to read.
                
                Question: {question}
                
                Answer:
            """)
            
            try:
                chain = prompt | self.llm
                response = chain.invoke({"question": query_text})
                answer = response.content
            except Exception as e:
                answer = (
                    "I'm having a bit of trouble connecting to my creative brain right now. "
                    "However, for official advice, please visit the NCSC website at ncsc.gov.uk."
                )
        else:
            answer = (
                "I see that my local AI engine isn't running, so I can't chat right now. "
                "Please ensure Ollama is setup and running."
            )
            
        return answer, sources
