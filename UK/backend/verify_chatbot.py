from rag import RAGPipeline

def test_chatbot():
    print("Initializing RAG Pipeline...")
    rag = RAGPipeline()
    
    # Test query based on one of the PDF titles/topics
    query = "What are the security best practices?"
    print(f"\nQuery: {query}")
    
    answer, sources = rag.query(query)
    
    print("\nAnswer:")
    print(answer)
    
    print("\nSources:")
    for source in sources:
        print(f"- {source['title']} ({source.get('type', 'unknown')})")

if __name__ == "__main__":
    test_chatbot()
