"""
Data Ingestion Script - Load UK cybersecurity data into ChromaDB.

This script is responsible for populating the vector database (ChromaDB) with knowledge.
It supports two primary data sources:
1. JSON files containing scraped web content (articles, reports).
2. PDF documents (whitepapers, official guidance) located in a specific directory.

The script handles:
- Reading and parsing source files.
- Cleaning and truncating text content.
- Generating metadata for source tracking.
- Batch uploading to ChromaDB to respect resource limits.
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def ingest_json_data(collection, json_path: str, region: str = "UK"):
    """
    Ingest data from a JSON file containing scraped web content.
    
    Args:
        collection: The ChromaDB collection object to insert data into.
        json_path (str): Path to the JSON file.
        region (str): Region tag to apply to metadata (default: "UK").
        
    Returns:
        int: The number of documents successfully ingested.
    """
    path = Path(json_path)
    if not path.exists():
        print(f"JSON file not found: {json_path}")
        return 0
    
    # Load JSON content
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("No data in JSON file")
        return 0
    
    # Lists to hold batch data
    ids = []
    documents = []
    metadatas = []
    
    # Iterate through each item in the scraped data
    for i, item in enumerate(data):
        url = item.get('url', '')
        content = item.get('content', '')
        
        # Validation: Skip empty or too short content to avoid noise
        if not content or len(content) < 100:
            continue
        
        # Truncation: Limit content length to prevent token overflow during embedding
        # Ideally, we should chunk this properly, but simple truncation works for now.
        if len(content) > 5000:
            content = content[:5000]
        
        # Title Extraction: Try to derive a readable title from the URL slug
        title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        if title == '' or title == 'Https:':
            title = f"UK Cybersecurity Article {i + 1}"
        
        # Generate a unique ID for the document
        doc_id = f"{region}_{path.stem}_{i}"
        
        ids.append(doc_id)
        # Format the document content to include the title for better context
        documents.append(f"{title}\n\n{content}")
        metadatas.append({
            "region": region,
            "source_url": url,
            "title": title,
            "type": item.get('type', 'html')
        })
    
    # Perform Batch Upsert
    if ids:
        # ChromaDB acts better with smaller batches (e.g., 100 items)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            collection.upsert(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
        print(f"Ingested {len(ids)} documents from JSON")
    
    return len(ids)


def ingest_pdf_data(collection, pdf_dir: str, region: str = "UK"):
    """
    Ingest data from all PDF files in a specified directory.
    Uses the 'process_pdf_directory' utility to handle text extraction and chunking.
    
    Args:
        collection: The ChromaDB collection object.
        pdf_dir (str): Directory containing PDF files.
        region (str): Region tag for metadata.
        
    Returns:
        int: The number of PDF chunks ingested.
    """
    # Import helper locally to avoid circular dependencies if any
    from pdf_processor import process_pdf_directory
    
    path = Path(pdf_dir)
    if not path.exists():
        print(f"PDF directory not found: {pdf_dir}")
        return 0
    
    # Extract and chunk text from PDFs
    documents = process_pdf_directory(str(path), region)
    
    if not documents:
        print("No PDFs to ingest")
        return 0
    
    # Unpack the processed document structures
    ids = [doc['id'] for doc in documents]
    contents = [doc['content'] for doc in documents]
    metadatas = [doc['metadata'] for doc in documents]
    
    # Batch Upsert
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_end = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:batch_end],
            documents=contents[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
    
    print(f"Ingested {len(ids)} chunks from PDFs")
    return len(ids)


def main():
    """
    Main execution entry point.
    Initializes the DB connection and triggers ingestion workflow.
    """
    # Initialize ChromaDB Persistent Client
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Setup Embedding Function
    # 'all-MiniLM-L6-v2' is a fast and effective model for sentence embeddings
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create or Get the Collection
    collection = client.get_or_create_collection(
        name="uk_cyber_knowledge",
        embedding_function=ef
    )
    
    print(f"Collection has {collection.count()} existing documents")
    
    # Step 1: Ingest valid JSON Scraped Data
    # Points to the specific scraped file for this region
    json_path = os.getenv("JSON_DATA_PATH", "../../cyber_chatbot_UK1.json")
    json_count = ingest_json_data(collection, json_path)
    
    # Step 2: Ingest PDFs
    # Checks specific './pdfs' directory for any additional documents
    pdf_dir = "./pdfs"
    if Path(pdf_dir).exists():
        pdf_count = ingest_pdf_data(collection, pdf_dir)
    else:
        pdf_count = 0
        print(f"No PDF directory found at {pdf_dir}. Create it and add PDFs to ingest.")
    
    # Summary Report
    print(f"\n=== Ingestion Complete ===")
    print(f"JSON documents: {json_count}")
    print(f"PDF chunks: {pdf_count}")
    print(f"Total in collection: {collection.count()}")


if __name__ == "__main__":
    main()
