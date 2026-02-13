"""
PDF Processor Module

This module is responsible for extracting clean text from PDF documents and splitting it into 
manageable chunks for the Retrieval Augmented Generation (RAG) system.

Key Features:
- Dual-engine extraction: Falls back to PyPDF2 if pdfplumber fails.
- Text cleaning: Removes noise like headers, footers, and fragmented URLs.
- Intelligence Chunking: Splits text into overlapping segments to preserve context boundaries.
"""

from pathlib import Path
from typing import List, Dict
import re


def extract_text_pypdf2(pdf_path: str) -> str:
    """
    Extract text using PyPDF2 library.
    Generally faster but less robust with complex layouts.
    """
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
    """
    Extract text using pdfplumber library.
    Better at handling multi-column layouts and tables.
    """
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
    """
    Sanitize extracted text to improve embedding quality.
    
    Operations:
    - Collapses multiple whitespace characters into single spaces.
    - Removes common footer patterns like 'Page X of Y'.
    - Fixes broken URL patterns often caused by line breaks in PDFs.
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove page numbers and headers
    text = re.sub(r'Page \d+ of \d+', '', text)
    # Remove URLs that are fragmented (e.g. http : // ...)
    text = re.sub(r'http\s*:\s*/\s*/\s*', 'https://', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text (str): The full text content.
        chunk_size (int): Target number of words per chunk.
        overlap (int): Number of words to overlap between chunks to maintain context.
        
    Returns:
        List[str]: A list of text chunks.
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        # Create chunk
        chunk = ' '.join(words[i:i + chunk_size])
        
        # Validation: Skip very short chunks that may not have enough context
        if len(chunk) > 100:  
            chunks.append(chunk)
    
    return chunks


def process_pdf(pdf_path: str, region: str = "UK", title: str = None) -> List[Dict]:
    """
    Workflow to fully process a single PDF file for RAG ingestion.
    
    Steps:
    1. Extract text (trying multiple engines).
    2. Clean text.
    3. Split into chunks.
    4. Wrap chunks with metadata (ID, Source, Title).
    
    Returns:
        List[Dict]: List of document objects ready for insertion into vector DB.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # 1. Extract Text Strategy
    # Try pdfplumber first (higher quality), fall back to PyPDF2
    text = extract_text_pdfplumber(pdf_path)
    if not text:
        text = extract_text_pypdf2(pdf_path)
    
    if not text:
        raise ValueError(f"Could not extract text from {pdf_path}")
    
    # 2. Clean
    text = clean_text(text)
    
    # 3. Chunk
    chunks = chunk_text(text)
    
    # 4. Build Document Objects
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
    """
    Batch process all PDF files in a given directory.
    Useful for bulk ingestion.
    """
    path = Path(directory)
    all_documents = []
    
    # Glob for all .pdf files
    for pdf_file in path.glob("*.pdf"):
        try:
            documents = process_pdf(str(pdf_file), region)
            all_documents.extend(documents)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    return all_documents


if __name__ == "__main__":
    # Test block: allows running this script standalone to test a specific PDF
    import sys
    if len(sys.argv) > 1:
        docs = process_pdf(sys.argv[1])
        print(f"Extracted {len(docs)} chunks")
        if docs:
            print(f"First chunk: {docs[0]['content'][:200]}...")
