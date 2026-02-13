"""
UK Cybersecurity Backend - FastAPI Server

This script initializes and runs the backend API server using FastAPI.
It serves as the bridge between the frontend application and the backend logic (RAG pipeline, Data updates).

Key responsibilities:
- Hosting API endpoints for Chatbot queries (/api/query).
- checking for updates from scraped sources (/api/updates).
- Serving article data to the frontend news feed (/api/articles).
- Providing health status checks (/api/health).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

from update_checker import UpdateChecker
from rag import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="UK Cybersecurity API",
    description="Backend for UK Cybersecurity Intelligence Hub",
    version="1.0.0"
)

# ==========================================
# CORS Configuration
# ==========================================
# Allow Cross-Origin Resource Sharing so the frontend (running on a different port/domain)
# can make requests to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend domains
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# ==========================================
# Service Initialization
# ==========================================
# Initialize the Update Checker service with the path to the scraped data.
json_path = os.getenv("JSON_DATA_PATH", "../../cyber_chatbot_UK1.json")
update_checker = UpdateChecker(json_path)

# Initialize RAG Pipeline (Retrieval Augmented Generation)
# We use a try-except block here to ensure the server can still start even if the ML model fails to load.
rag_pipeline = None
try:
    rag_pipeline = RAGPipeline()
except Exception as e:
    print(f"Warning: RAG pipeline not initialized: {e}")


# ==========================================
# Data Models (Pydantic)
# ==========================================

class QueryRequest(BaseModel):
    """Request model for chatbot queries."""
    query: str
    region: Optional[str] = "UK"


class QueryResponse(BaseModel):
    """Response model for chatbot answers."""
    answer: str
    sources: List[dict]


class UpdateInfo(BaseModel):
    """Model for source update information."""
    url: str
    title: str
    has_new_content: bool
    last_checked: str


# ==========================================
# API Endpoints
# ==========================================

@app.get("/")
async def root():
    """Root endpoint to verify server status."""
    return {
        "status": "online",
        "service": "UK Cybersecurity API",
        "endpoints": ["/api/updates", "/api/query", "/api/health"]
    }


@app.get("/api/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "rag_available": rag_pipeline is not None,
        "update_checker_ready": update_checker.is_ready()
    }


@app.get("/api/updates")
async def check_updates(limit: int = 10):
    """
    Check source URLs for new content.
    Returns list of URLs that have been updated since last check.
    
    Args:
        limit (int): Maximum number of sources to check.
    """
    try:
        updates = await update_checker.check_for_updates(limit=limit)
        return {
            "total_sources": update_checker.total_sources,
            "checked": len(updates),
            "updates": updates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """
    Process a user's question about cybersecurity.
    Uses the RAG pipeline to retrieve relevant context and generate an answer.
    
    Args:
        request (QueryRequest): Contains the user's query and region context.
    
    Returns:
        QueryResponse: Generated answer and list of sources used.
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available. Run ingest.py first or checks logs."
        )
    
    try:
        # Pass query to RAG system
        answer, sources = rag_pipeline.query(request.query, request.region)
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
async def get_articles(limit: int = 10):
    """
    Retrieve article previews for the frontend news feed.
    Serves data directly from the processed JSON storage.
    
    Args:
        limit (int): Number of articles to return.
    """
    try:
        articles = update_checker.get_articles(limit=limit)
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the server using Uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
