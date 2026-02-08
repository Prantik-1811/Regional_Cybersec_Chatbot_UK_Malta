"""
Data Ingestion Script - Load UK cybersecurity data into ChromaDB.
Supports both JSON scraped content and PDF documents.
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


def ingest_json_data(collection, json_path: str, region: str = "UK"):
    """Ingest data from JSON file (scraped web content)."""
    path = Path(json_path)
    if not path.exists():
        print(f"JSON file not found: {json_path}")
        return 0
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print("No data in JSON file")
        return 0
    
    ids = []
    documents = []
    metadatas = []
    
    for i, item in enumerate(data):
        url = item.get('url', '')
        content = item.get('content', '')
        
        if not content or len(content) < 100:
            continue
        
        # Truncate very long content
        if len(content) > 5000:
            content = content[:5000]
        
        # Extract title from content or URL
        title = url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
        if title == '' or title == 'Https:':
            title = f"UK Cybersecurity Article {i + 1}"
        
        doc_id = f"{region}_{i}"
        ids.append(doc_id)
        documents.append(f"{title}\n\n{content}")
        metadatas.append({
            "region": region,
            "source_url": url,
            "title": title,
            "type": item.get('type', 'html')
        })
    
    if ids:
        # Batch upsert (ChromaDB has limits)
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
    """Ingest data from PDF files."""
    from pdf_processor import process_pdf_directory
    
    path = Path(pdf_dir)
    if not path.exists():
        print(f"PDF directory not found: {pdf_dir}")
        return 0
    
    documents = process_pdf_directory(str(path), region)
    
    if not documents:
        print("No PDFs to ingest")
        return 0
    
    ids = [doc['id'] for doc in documents]
    contents = [doc['content'] for doc in documents]
    metadatas = [doc['metadata'] for doc in documents]
    
    # Batch upsert
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
    # Initialize ChromaDB
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Embedding function
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="uk_cyber_knowledge",
        embedding_function=ef
    )
    
    print(f"Collection has {collection.count()} existing documents")
    
    # Ingest JSON data
    json_path = os.getenv("JSON_DATA_PATH", "../../cyber_chatbot_UK1.json")
    json_count = ingest_json_data(collection, json_path)
    
    # Ingest PDFs (if any exist)
    pdf_dir = "./pdfs"
    if Path(pdf_dir).exists():
        pdf_count = ingest_pdf_data(collection, pdf_dir)
    else:
        pdf_count = 0
        print(f"No PDF directory found at {pdf_dir}. Create it and add PDFs to ingest.")
    
    print(f"\n=== Ingestion Complete ===")
    print(f"JSON documents: {json_count}")
    print(f"PDF chunks: {pdf_count}")
    print(f"Total in collection: {collection.count()}")


if __name__ == "__main__":
    main()
