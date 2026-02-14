"""
UK Cybersecurity Backend - FastAPI Server
Provides APIs for update checking, chatbot queries, and content ingestion.
"""

"""
Imported Libraries Explanation:

fastapi                → Main web framework used to build the API server.
HTTPException          → Used to return structured HTTP error responses.
StreamingResponse      → Enables streaming responses (used for real-time chatbot output).
CORSMiddleware         → Allows frontend applications from other origins to access the API.
pydantic.BaseModel     → Used for defining request and response data validation models.
typing.Optional        → Allows optional request parameters.
typing.List            → Used for defining list types in response models.
os                     → Access environment variables and system-level configuration.
dotenv.load_dotenv     → Loads environment variables from a .env file.
update_checker         → Custom module that checks if source URLs have updated content.
rag.RAGPipeline        → Custom Retrieval-Augmented Generation pipeline for chatbot responses.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from update_checker import UpdateChecker
from rag import RAGPipeline

# Load environment variables
load_dotenv()

# Create FastAPI application instance
app = FastAPI(
    title="UK Cybersecurity API",
    description="Backend for UK Cybersecurity Intelligence Hub",
    version="1.0.0"
)

# ---------------------------------------------------------
# 🔹 CORS Configuration
# ---------------------------------------------------------
# Allows frontend applications (any origin) to access backend APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (for development flexibility)
    allow_credentials=True,
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)

# ---------------------------------------------------------
# 🔹 Service Initialisation
# ---------------------------------------------------------

# Path to JSON knowledge base (configurable via environment variable)
json_path = os.getenv("JSON_DATA_PATH", "../../Scraped files")

# Initialise update checker (monitors content changes)
update_checker = UpdateChecker(json_path)

# Initialise RAG pipeline (semantic search + LLM)
rag_pipeline = None

# Attempt to initialise RAG pipeline safely
try:
    rag_pipeline = RAGPipeline()
except Exception as e:
    # If RAG fails, API still runs but chatbot won't be available
    print(f"Warning: RAG pipeline not initialized: {e}")


# ---------------------------------------------------------
# 🔹 Request / Response Models
# ---------------------------------------------------------

# Request model for chatbot queries
class QueryRequest(BaseModel):
    query: str                 # User question
    region: Optional[str] = "UK"  # Region context (default UK)


# Structured response model for chatbot answers
class QueryResponse(BaseModel):
    answer: str                # Generated answer
    sources: List[dict]        # List of supporting sources


# Model representing update information for a source
class UpdateInfo(BaseModel):
    url: str
    title: str
    has_new_content: bool
    last_checked: str


# ---------------------------------------------------------
# 🔹 Root Endpoint
# ---------------------------------------------------------
# Basic service info endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "UK Cybersecurity API",
        "endpoints": ["/api/updates", "/api/query", "/api/health"]
    }


# ---------------------------------------------------------
# 🔹 Health Check Endpoint
# ---------------------------------------------------------
# Used to verify backend system health
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        # Indicates whether RAG system is available
        "rag_available": rag_pipeline is not None,
        # Indicates whether update checker is ready
        "update_checker_ready": update_checker.is_ready()
    }


# ---------------------------------------------------------
# 🔹 Update Checking Endpoint
# ---------------------------------------------------------
@app.get("/api/updates")
async def check_updates(limit: int = 10):
    """
    Check source URLs for new content.
    Returns list of URLs that have been updated since last check.
    """
    try:
        # Asynchronously check for updates in source content
        updates = await update_checker.check_for_updates(limit=limit)

        return {
            "total_sources": update_checker.total_sources,
            "checked": len(updates),
            "updates": updates
        }

    # Handle unexpected failures gracefully
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# 🔹 Streaming Chat Endpoint
# ---------------------------------------------------------
@app.post("/chat")
def chat(req: QueryRequest):
    # Ensure RAG pipeline is available
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available."
        )

    # Stream token-by-token response to client
    return StreamingResponse(
        rag_pipeline.query_stream(req.query, req.region),
        media_type="text/plain"
    )


# ---------------------------------------------------------
# 🔹 Standard Chat Query Endpoint
# ---------------------------------------------------------
@app.post("/api/query", response_model=QueryResponse)
async def query_chatbot(request: QueryRequest):
    """
    Query the chatbot with a cybersecurity question.
    Uses RAG pipeline with UK government sources.
    """
    # Ensure RAG pipeline is initialised
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available. Run ingest.py first."
        )
    
    try:
        # Perform semantic retrieval + LLM generation
        answer, sources = rag_pipeline.query(request.query, request.region)

        # Return structured response
        return QueryResponse(answer=answer, sources=sources)

    # Handle runtime errors safely
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# 🔹 Articles Endpoint
# ---------------------------------------------------------
@app.get("/api/articles")
async def get_articles(limit: int = 10):
    """
    Get articles from the JSON data for display.
    """
    try:
        # Retrieve articles from update checker
        articles = update_checker.get_articles(limit=limit)

        return {"articles": articles}

    # Handle errors gracefully
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# 🔹 Run Server Directly (Development Mode)
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    # Start FastAPI server on port 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)
