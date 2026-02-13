"""
RAG Pipeline - Retrieval-Augmented Generation for UK Cybersecurity chatbot.

This module manages the interaction between the Vector Database (ChromaDB) and the Large Language Model (Ollama).
It is responsible for:
1. Connecting to the knowledge base.
2. Managing the LLM session.
3. Processing user queries and generating responses.

Target Architecture:
User Query -> Embedding -> Vector Search (ChromaDB) -> Context + Query -> LLM -> Answer
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()


class RAGPipeline:
    def __init__(self):
        """
        Initialize the RAG pipeline.
        Sets up the database client and the LLM connection.
        """
        # Paths and Configurations
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        # Embedding Function
        # We use the same model as ingestion to ensure vector space compatibility.
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Database Collection
        # Try to load existing knowledge base, create new if missing.
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
        
        # LLM Setup (Ollama)
        # We use a local instance of Llama 3 for privacy and offline capability.
        self.llm = None
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            from langchain_ollama import ChatOllama
            from langchain_core.prompts import ChatPromptTemplate
            
            self.llm = ChatOllama(
                model="llama3.2",
                temperature=0, # Low temperature for factual consistency
                base_url=ollama_base_url
            )
            self.ChatPromptTemplate = ChatPromptTemplate
            print(f"Connected to Ollama at {ollama_base_url}")
        except Exception as e:
            print(f"Warning: Ollama not available: {e}. Chatbot will not function correctly.")
    
    def query(self, query_text: str, region: str = "UK"):
        """
        Process a user query.
        
        Current Implementation:
        - Uses a Direct LLM Chat approach (Zero-Shot).
        - To enable full RAG, uncomment the retrieval logic below.
        
        Args:
            query_text (str): The user's question.
            region (str): Context region (reserved for future filtering).
            
        Returns:
            tuple: (Answer String, List of Source Dictionaries)
        """
        
        # Default static sources for safety/fallback
        sources = [
            {"url": "https://www.ncsc.gov.uk", "title": "National Cyber Security Centre (NCSC)", "type": "official"},
            {"url": "https://www.actionfraud.police.uk", "title": "Action Fraud", "type": "official"}
        ]
        
        answer = ""
        
        # Check if LLM is ready
        if self.llm:
            # Prompt Engineering
            # We define a persona "CyberSafe AI" to guide the model's tone and style.
            prompt = self.ChatPromptTemplate.from_template("""
                You are "CyberSafe AI", a friendly and knowledgeable UK cybersecurity expert assistant.
                
                Your goal is to have a natural, helpful conversation with the user about online safety and cyber threats.
                
                IMPORTANT GUIDELINES:
                - Be conversational, empathetic, and clear.
                - Use British English spelling (e.g., 'organisation', 'defence', 'behaviour').
                - You can discuss any cybersecurity topic freely using your own knowledge.
                - If asked about reporting a crime, always recommend Action Fraud.
                - Keep your answers concise and easy to read.
                
                User Question: {question}
                
                Your Answer:
            """)
            
            try:
                # Chain Execution: Prompt -> LLM
                chain = prompt | self.llm
                response = chain.invoke({"question": query_text})
                answer = response.content
            except Exception as e:
                # Fail gracefully if inference fails
                answer = (
                    "I'm having a bit of trouble connecting to my creative brain right now. "
                    "However, for official advice, please visit the NCSC website at ncsc.gov.uk."
                )
        else:
            # Fallback if Ollama is not initialized
            answer = (
                "I see that my local AI engine isn't running, so I can't chat right now. "
                "Please ensure Ollama is setup and running."
            )
            
        return answer, sources
