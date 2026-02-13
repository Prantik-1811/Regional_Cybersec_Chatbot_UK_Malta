"""
UK Cybersecurity Backend - FastAPI Server
Provides APIs for update checking, chatbot queries, and content ingestion.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
import traceback

from update_checker import UpdateChecker
from rag import RAGPipeline

load_dotenv()

app = FastAPI(
    title="UK Cybersecurity API",
    description="Backend for UK Cybersecurity Intelligence Hub",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
json_path = os.getenv("JSON_DATA_PATH", "../../cyber_chatbot_UK1.json")
update_checker = UpdateChecker(json_path)
rag_pipeline = None

try:
    rag_pipeline = RAGPipeline()
except Exception as e:
    print(f"Warning: RAG pipeline not initialized: {e}")


class QueryRequest(BaseModel):
    query: str
    region: Optional[str] = "UK"


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


class UpdateInfo(BaseModel):
    url: str
    title: str
    has_new_content: bool
    last_checked: str


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "UK Cybersecurity API",
        "endpoints": ["/api/updates", "/api/query", "/api/health"]
    }


@app.get("/api/health")
async def health():
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
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available. Run ingest.py first."
        )
    
    try:
        answer, sources = rag_pipeline.query(request.query, request.region)
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        traceback.print_exc()  # 👈 This prints the real error
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles")
async def get_articles(limit: int = 10):
    """
    Get articles from the JSON data for display.
    """
    try:
        articles = update_checker.get_articles(limit=limit)
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
