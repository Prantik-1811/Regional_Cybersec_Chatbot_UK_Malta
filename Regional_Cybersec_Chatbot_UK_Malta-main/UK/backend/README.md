# UK Cybersecurity Backend

Python backend for the UK Cybersecurity website with:
- Update checking for source URLs
- PDF processing for RAG
- Chatbot API with Ollama integration

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/updates` | GET | Check for new content from source URLs |
| `/api/query` | POST | Query chatbot with UK cybersecurity questions |
| `/api/ingest` | POST | Ingest new PDFs/content into knowledge base |
