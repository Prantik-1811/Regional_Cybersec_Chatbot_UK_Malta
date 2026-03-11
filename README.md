> Cyber Warrior Program | DeepCytes Cyber Labs (UK)

## Program Attribution & Disclaimer

This repository was created as part of the **Cyber Warrior Program** conducted by  
**DeepCytes Cyber Labs (UK)**.

The Cyber Warrior Program is an educational and mentorship-driven initiative focused on:
- AI literacy
- Cybersecurity awareness
- Ethical research practices
- Responsible use of emerging technologies

All work contained in this repository is produced **solely for educational and research purposes**.

### Legal & Ethical Notice
- No confidential, proprietary, or classified information was used.
- No malicious intent, exploitation, or unlawful activity is endorsed or performed.
- AI-generated outputs are experimental and may be incomplete or inaccurate.
- The responsibility for interpretation and usage of this content lies with the contributor.

**DeepCytes Cyber Labs (UK)** and its affiliates:
- Do not guarantee the accuracy of AI-generated content
- Are not liable for misuse of any information contained herein
- Do not endorse deployment of this work in production or offensive environments

### Mentorship & Attribution
This repository is published under mentorship provided through the  
**Cyber Warrior Program by DeepCytes Cyber Labs (UK)**.

The purpose of public publication is:
- Skill demonstration
- Transparent learning
- Knowledge sharing within ethical and legal boundaries

© DeepCytes Cyber Labs (UK). All rights reserved.

---

# 🛡️ Regional Cybersecurity Chatbot — UK & Malta

A comprehensive cybersecurity intelligence platform featuring an interactive dashboard, an AI chatbot powered by a Retrieval-Augmented Generation (RAG) pipeline, and a live threat map. Built for the UK and Malta regions.

---

# 📸 Key Features

| Feature | Description |
|---------|-------------|
| **📰 Live News Feed** | Aggregates cybersecurity news from official UK government sources (NCSC, Action Fraud, ICO, GOV.UK) and displays them in a responsive card grid. |
| **🌍 Live Threat Map** | Interactive global threat visualization with SVG + Canvas animations showing real-time cyber attack simulations. Attack counts persist on the server so counters resume after reload. |
| **📍 Interactive Reporting Map** | Clickable UK regional SVG map showing cybercrime reporting centres with phone numbers, websites, and addresses. |
| **💬 AI Chatbot** | Floating chatbot widget powered by a local LLM (Ollama + Llama 3.2) with Retrieval-Augmented Generation (RAG) grounding. |
| **📊 Data-Driven Stats** | Animated counters and statistics on cyber threats, incidents, and response times. |
| **🌗 Dark / Light Theme** | Toggle between dark and light mode across the entire dashboard. |
| **🇲🇹 Malta Chatbot** | Separate Malta-specific chatbot interface accessible from the landing page. |

---

# 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              Browser (Frontend)             │
│  index.html + main.js + chatbot.js + CSS    │
│                                             │
│  Interactive SVG Map ──postMessage──▶ JS    │
│  Chatbot Widget ──fetch──▶ Backend API      │
└────────────────────┬────────────────────────┘
                     │ HTTP (port 8001)
┌────────────────────▼────────────────────────┐
│          FastAPI Backend (Python)            │
│                                             │
│  /api/query    → RAG Pipeline → Ollama LLM  │
│  /api/updates  → Update Checker (scraper)   │
│  /api/articles → JSON data store            │
│  /api/attack-stats → Persistent stats file  │
│  /api/health   → Status check               │
│                                             │
│  ChromaDB (Vector Store)                    │
│  Sentence-Transformers (Embeddings)         │
└────────────────────┬────────────────────────┘
                     │
              ┌──────▼──────┐
              │   Ollama     │
              │  llama3.2    │
              │ (port 11434) │
              └──────────────┘
```

---

# 📋 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.8+ | Backend server and RAG pipeline |
| **pip** | Latest | Python package manager |
| **Ollama** | Latest | Local LLM inference engine |
| **Git** | Latest | Cloning the repository |
| **Modern Browser** | Chrome / Edge / Firefox | Frontend dashboard |

> Ollama must be installed and running with the `llama3.2` model pulled before starting the backend.

---

# 🚀 Setup & Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Prantik-1811/Regional_Cybersec_Chatbot_UK_Malta.git
cd Regional_Cybersec_Chatbot_UK_Malta
```

---

## 2. Create a Python Virtual Environment

```bash
python -m venv .venv
```

### Activate

**Windows (PowerShell)**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD)**

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
cd UK/backend
pip install -r requirements.txt
```

---

## 4. Install & Configure Ollama

Download from:

https://ollama.com/download

Pull the LLM model:

```bash
ollama pull llama3.2
```

Verify installation:

```bash
ollama list
```

You should see **llama3.2** listed.

---

# 📦 Ingest Data into the Vector Database

Before the chatbot can answer questions, populate the ChromaDB vector store:

```bash
cd UK/backend
python ingest.py
```

This will:

- Read scraped JSON data
- Chunk and embed documents
- Generate embeddings using **all-MiniLM-L6-v2**
- Store vectors in **chroma_db**

---

# ▶️ Running the Application

## Option A: One-Click Launch (Windows)

Double-click:

```
run_chatbot.bat
```

This will:

1. Start FastAPI backend server
2. Wait a few seconds
3. Open the dashboard in your browser

---

## Option B: Manual Startup

Start backend:

```bash
cd UK/backend
python main.py
```

Expected output:

```
Loaded collection with N chunks
Connected to Ollama at http://localhost:11434
INFO: Uvicorn running on http://0.0.0.0:8001
```

Open frontend:

```
UK/index.html
```

---

# 📂 Project Structure

```
Regional_Cybersec_Chatbot_UK_Malta/
├── UK/
│   ├── index.html
│   ├── scripts/
│   │   ├── main.js
│   │   └── chatbot.js
│   ├── styles/
│   │   ├── main.css
│   │   └── cyber-map.css
│   ├── assets/
│   │   ├── uk-map.svg
│   │   └── world-map.svg
│   └── backend/
│       ├── main.py
│       ├── rag.py
│       ├── ingest.py
│       ├── update_checker.py
│       ├── pdf_processor.py
│       ├── train_chatbot.py
│       ├── verify_chatbot.py
│       ├── requirements.txt
│       ├── attack_stats.json
│       └── chroma_db/
│
├── Malta/
│   ├── index.html
│   ├── Scripts/
│   └── Styles/
│
├── Scraped files/
├── Training_Data/
├── tools/
│   ├── gather_data.py
│   ├── inspect_pdfs.py
│   ├── inspect_pdfs_v2.py
│   ├── debug_api.py
│   └── debug_json.py
│
├── run_chatbot.bat
├── README.md
└── world.svg
```

---

# 🔌 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status |
| `/api/health` | GET | Health check |
| `/api/query` | POST | Chat with the AI |
| `/api/updates` | GET | Check sources for new content |
| `/api/articles` | GET | Retrieve news articles |
| `/api/attack-stats` | GET | Retrieve attack stats |
| `/api/attack-stats` | POST | Save attack stats |

Interactive docs available at:

```
http://localhost:8001/docs
```

---

# ⚙️ Configuration

Environment variables inside:

```
UK/backend/.env
```

Example:

```
OLLAMA_BASE_URL=http://localhost:11434
JSON_DATA_PATH=../../Scraped files/cyber_chatbot_UK1.json
CHROMA_DB_PATH=./chroma_db
```

---

# 🛠 Troubleshooting

### Chatbot says "I'm currently offline"

Ensure backend is running:

```bash
python main.py
```

---

### Backend starts but RAG says "not initialized"

Run ingestion:

```bash
python ingest.py
```

---

### "Error calling LLM: Connection refused"

Start Ollama:

```bash
ollama serve
```

Verify:

```bash
ollama list
```

---

# 🤝 Data Sources & Partners

| Source | URL |
|------|------|
| National Cyber Security Centre (NCSC) | https://www.ncsc.gov.uk |
| Action Fraud | https://www.actionfraud.police.uk |
| Information Commissioner's Office (ICO) | https://ico.org.uk |
| GOV.UK Cyber Security | https://www.gov.uk/government/topics/cyber-security |

---

# 📄 License

This project is developed for the **Regional Cybersecurity Chatbot — UK & Malta** academic project.

---

*Built with FastAPI, ChromaDB, Ollama, and vanilla HTML/CSS/JS.*
