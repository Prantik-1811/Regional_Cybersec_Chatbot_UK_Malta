"""
Data Ingestion Script - Load UK cybersecurity data into ChromaDB.
Improved version with smart chunking for better RAG retrieval quality.
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
# CONFIG
# =========================
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
JSON_FOLDER = os.getenv("JSON_DATA_FOLDER", "../../")
COLLECTION_NAME = "uk_cyber_knowledge"
EMBED_MODEL = "all-MiniLM-L6-v2"


# =========================
# TEXT CHUNKING
# =========================
def chunk_text(text, chunk_size=800, overlap=150):
    """
    Split text into overlapping chunks.
    Helps preserve numbered steps and context continuity.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# =========================
# JSON INGESTION
# =========================
def ingest_json_data(collection, json_path: Path, region: str = "UK"):
    """Ingest data from a single JSON file with smart chunking."""

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

        if not content or len(content) < 200:
            continue

        # Clean excessive whitespace
        content = " ".join(content.split())

        # Generate title from URL
        title = url.split("/")[-1].replace("-", " ").replace("_", " ").title()
        if not title or title.lower().startswith("http"):
            title = f"UK Cybersecurity Article {i + 1}"

        # Create chunks
        chunks = chunk_text(content)

        for chunk_index, chunk in enumerate(chunks):
            doc_id = f"{region}_{json_path.stem}_{i}_{chunk_index}"

            ids.append(doc_id)

            # Include title in document body to strengthen retrieval
            documents.append(f"{title}\n\n{chunk}")

            metadatas.append({
                "region": region,
                "source_url": url,
                "title": title,
                "type": item.get("type", "html")
            })

            chunk_counter += 1

    # Batch upsert for performance
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
# MAIN
# =========================
def main():
    print("=== Starting Ingestion ===")

    # Clean rebuild (prevents embedding mismatch issues)
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

    # Load all UK JSON files
    json_files = list(Path(JSON_FOLDER).glob("cyber_chatbot_UK*.json"))

    if not json_files:
        print("No JSON files found.")
        return

    total_chunks = 0

    for json_file in json_files:
        total_chunks += ingest_json_data(collection, json_file)

    print("\n=== Ingestion Complete ===")
    print(f"Total chunks ingested: {total_chunks}")
    print(f"Total in collection: {collection.count()}")


if __name__ == "__main__":
    main()
