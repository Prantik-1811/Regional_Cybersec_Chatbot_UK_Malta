"""
PDF Processor - Extract and chunk text from PDFs for RAG ingestion.
Supports both PyPDF2 and pdfplumber for maximum compatibility.
"""

from pathlib import Path
from typing import List, Dict
import re


def extract_text_pypdf2(pdf_path: str) -> str:
    """Extract text using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"PyPDF2 extraction failed: {e}")
        return ""


def extract_text_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (better for complex layouts)."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
        return ""


def clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove page numbers and headers
    text = re.sub(r'Page \d+ of \d+', '', text)
    # Remove URLs that are fragmented
    text = re.sub(r'http\s*:\s*/\s*/\s*', 'https://', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk) > 100:  # Skip very short chunks
            chunks.append(chunk)
    
    return chunks


def process_pdf(pdf_path: str, region: str = "UK", title: str = None) -> List[Dict]:
    """
    Process a PDF file for RAG ingestion.
    
    Returns list of document chunks with metadata.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Extract text (try pdfplumber first, fall back to PyPDF2)
    text = extract_text_pdfplumber(pdf_path)
    if not text:
        text = extract_text_pypdf2(pdf_path)
    
    if not text:
        raise ValueError(f"Could not extract text from {pdf_path}")
    
    # Clean and chunk
    text = clean_text(text)
    chunks = chunk_text(text)
    
    # Build documents
    doc_title = title or path.stem.replace('_', ' ').replace('-', ' ').title()
    documents = []
    
    for i, chunk in enumerate(chunks):
        documents.append({
            "id": f"{region}_{path.stem}_{i}",
            "content": chunk,
            "metadata": {
                "region": region,
                "source_url": f"file://{path.absolute()}",
                "title": f"{doc_title} (Part {i + 1})",
                "type": "pdf",
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        })
    
    print(f"Processed {pdf_path}: {len(chunks)} chunks")
    return documents


def process_pdf_directory(directory: str, region: str = "UK") -> List[Dict]:
    """Process all PDFs in a directory."""
    path = Path(directory)
    all_documents = []
    
    for pdf_file in path.glob("*.pdf"):
        try:
            documents = process_pdf(str(pdf_file), region)
            all_documents.extend(documents)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    return all_documents


if __name__ == "__main__":
    # Test with sample PDF
    import sys
    if len(sys.argv) > 1:
        docs = process_pdf(sys.argv[1])
        print(f"Extracted {len(docs)} chunks")
        if docs:
            print(f"First chunk: {docs[0]['content'][:200]}...")
