"""
Chatbot Training Script

This script orchestrates the full knowledge ingestion process.
It is intended to be run manually or via a scheduler to update the chatbot's knowledge base.

Workflow:
1. Connects to ChromaDB.
2. Scans for scraped JSON data files.
3. Scans for PDF training documents.
4. Feeds all found content into the ingestion modules.
"""

import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from ingest import ingest_json_data, ingest_pdf_data

# Load environment configuration
load_dotenv()

def train_chatbot():
    print("=== Starting Chatbot Training (Ingestion) ===")
    
    # 1. Configuration & Paths
    # We use absolute paths where possible to avoid CWD confusion during execution
    base_dir = r"d:\Prantik\Chatbot_Deepcytes"
    scraped_dir = os.path.join(base_dir, "Scraped files")
    pdf_dir = os.path.join(base_dir, "Training_Data", "PDFs")
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    print(f"Data Source (JSON): {scraped_dir}")
    print(f"Data Source (PDF):  {pdf_dir}")
    print(f"ChromaDB Path:    {chroma_path}")

    # 2. Database Initialization
    # Connect to the persistent vector store
    client = chromadb.PersistentClient(path=chroma_path)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Retrieve the collection
    collection = client.get_or_create_collection(
        name="uk_cyber_knowledge",
        embedding_function=ef
    )
    
    initial_count = collection.count()
    print(f"Initial document count: {initial_count}")

    # 3. Ingest JSON Files (Scraped Content)
    # Glob allows us to pick up multiple updates (e.g., cyber_chatbot_UK1.json, UK2.json, etc.)
    json_files = glob.glob(os.path.join(scraped_dir, "*.json"))
    print(f"\nFound {len(json_files)} JSON files.")
    
    total_json_docs = 0
    for json_file in json_files:
        print(f"Ingesting: {os.path.basename(json_file)}")
        try:
            count = ingest_json_data(collection, json_file)
            total_json_docs += count
        except Exception as e:
            print(f"Error ingesting {json_file}: {e}")

    # 4. Ingest PDF Files (Documents)
    # Checks if the training data directory exists before attempting
    if os.path.exists(pdf_dir):
        print("\nIngesting PDFs...")
        try:
            pdf_count = ingest_pdf_data(collection, pdf_dir)
        except Exception as e:
            print(f"Error ingesting PDFs: {e}")
            pdf_count = 0
    else:
        print(f"\nPDF directory not found: {pdf_dir}")
        pdf_count = 0

    # 5. Summary Report
    final_count = collection.count()
    print("\n=== Training Complete ===")
    print(f"Documents added from JSONs: {total_json_docs}")
    print(f"Chunks added from PDFs:     {pdf_count}")
    print(f"Final collection count:     {final_count}")
    print(f"Net increase:               {final_count - initial_count}")

if __name__ == "__main__":
    train_chatbot()
