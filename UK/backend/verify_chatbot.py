"""
Chatbot Verification Script

Run this script to test if the RAG pipeline is initialized correctly.
It performs a simple query to the backend and prints the response and sources.

Usage:
    python verify_chatbot.py
"""

from rag import RAGPipeline

def test_chatbot():
    print("Initializing RAG Pipeline...")
    # This triggers the vector DB load and LLM connection
    rag = RAGPipeline()
    
    # Verification Query
    query = "What are the security best practices?"
    print(f"\nQuery: {query}")
    
    try:
        answer, sources = rag.query(query)
        
        print("\nAnswer:")
        print("-------")
        print(answer)
        print("-------")
        
        print("\nSources Used:")
        for source in sources:
            print(f"- {source['title']} ({source.get('type', 'unknown')})")
            
    except Exception as e:
        print(f"\nERROR: Chatbot verification failed.")
        print(f"Details: {e}")

if __name__ == "__main__":
    test_chatbot()
