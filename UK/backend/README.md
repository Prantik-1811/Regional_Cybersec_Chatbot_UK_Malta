# UK Cybersecurity Backend

Python backend for the UK Cybersecurity website with:
- Update checking for source URLs
- PDF processing for RAG
- Chatbot API with Ollama integration
- **Persistent live attack stats** — saved to `attack_stats.json`, survives server restarts

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
| `/api/articles` | GET | Retrieve news articles (static + RSS) |
| `/api/attack-stats` | GET | Retrieve persisted live attack map statistics |
| `/api/attack-stats` | POST | Save current attack stats snapshot from frontend |
| `/api/health` | GET | Health check (RAG + Ollama status) |

