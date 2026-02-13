"""
Data Ingestion Script - Load UK cybersecurity data into ChromaDB.
Improved version with smart chunking for better RAG retrieval quality.

This script manages the knowledge base creation process:
1. Cleans existing data (Full Rebuild).
2. Chunks text content into overlapping segments to preserve context.
3. Ingests scraped JSON data into the Vector Database (ChromaDB).
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
import os
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =========================
# CONFIGURATION
# =========================
# Paths and Model Settings
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
JSON_FOLDER = os.getenv("JSON_DATA_FOLDER", "../../")
COLLECTION_NAME = "uk_cyber_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"


# =========================
# TEXT CHUNKING LOGIC
# =========================
def chunk_text(text, chunk_size=800, overlap=150):
    """
    Split text into overlapping chunks.
    
    Why this is needed:
    - Large documents confuse the embedding model if passed as one block.
    - Overlap ensures that context (like a sentence bridging two chunks) isn't lost.
    
    Args:
        text (str): Raw text content.
        chunk_size (int): Character count per chunk.
        overlap (int): Number of characters to share between valid chunks.
        
    Returns:
        list: List of text string segments.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move forward by size minus overlap to create the sliding window effect
        start += chunk_size - overlap

    return chunks


# =========================
# JSON INGESTION MODULE
# =========================
def ingest_json_data(collection, json_path: Path, region: str = "UK"):
    """
    Ingest data from a single JSON file with smart chunking.
    
    Process:
    1. Read JSON file.
    2. Clean and Validate content.
    3. Generate chunks.
    4. batch Upload to ChromaDB.
    """

    if not json_path.exists():
        print(f"File not found: {json_path}")
        return 0

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print(f"No data in {json_path.name}")
        return 0

    ids = []
    documents = []
    metadatas = []
    chunk_counter = 0

    for i, item in enumerate(data):
        url = item.get("url", "")
        content = item.get("content", "")

        # Skip thin content that is likely noise
        if not content or len(content) < 200:
            continue

        # Clean excessive whitespace to save tokens
        content = " ".join(content.split())

        # Generate a human-readable title from the URL if missing
        title = url.split("/")[-1].replace("-", " ").replace("_", " ").title()
        if not title or title.lower().startswith("http"):
            title = f"UK Cybersecurity Article {i + 1}"

        # Create Chunks
        # We split the long article into smaller, retrievable pieces
        chunks = chunk_text(content)

        for chunk_index, chunk in enumerate(chunks):
            # Unique ID: Region + Filename + ArticleIndex + ChunkIndex
            doc_id = f"{region}_{json_path.stem}_{i}_{chunk_index}"

            ids.append(doc_id)

            # Context injection: Prepend Title to every chunk
            # This helps the model understand what the chunk is about even in isolation.
            documents.append(f"{title}\n\n{chunk}")

            metadatas.append({
                "region": region,
                "source_url": url,
                "title": title,
                "type": item.get("type", "html")
            })

            chunk_counter += 1

    # Batch upsert to DB
    # Processing in batches prevents memory issues and network timeouts
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size]
        )

    print(f"Ingested {chunk_counter} chunks from {json_path.name}")
    return chunk_counter


# =========================
# MAIN EXECUTION FLOW
# =========================
def main():
    print("=== Starting Ingestion ===")

    # Clean Rebuild Strategy
    # We delete the old DB to ensure no stale data remains (e.g., deleted articles).
    if Path(CHROMA_PATH).exists():
        print("Deleting existing ChromaDB folder for clean rebuild...")
        shutil.rmtree(CHROMA_PATH)

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef
    )

    print("Collection created.")

    # Locate Data Files
    json_files = list(Path(JSON_FOLDER).glob("cyber_chatbot_UK*.json"))

    if not json_files:
        print("No JSON files found at path: " + str(Path(JSON_FOLDER).absolute()))
        return

    total_chunks = 0

    # Run Ingestion
    for json_file in json_files:
        total_chunks += ingest_json_data(collection, json_file)

    print("\n=== Ingestion Complete ===")
    print(f"Total chunks ingested: {total_chunks}")
    print(f"Total in collection: {collection.count()}")


if __name__ == "__main__":
    main()
