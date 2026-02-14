# 🛡️ Regional Cybersecurity Chatbot — UK & Malta

A comprehensive cybersecurity intelligence platform featuring an interactive dashboard, an AI chatbot powered by a Retrieval-Augmented Generation (RAG) pipeline, and a live threat map. Built for the UK and Malta regions.

---

## 📸 Key Features

| Feature | Description |
|---------|-------------|
| **📰 Live News Feed** | Aggregates cybersecurity news from official UK government sources (NCSC, Action Fraud, ICO, GOV.UK) and displays them in a responsive card grid. |
| **🌍 Live Threat Map** | Interactive global threat visualization using SVG + Canvas animations showing real-time cyber attack simulations. |
| **📍 Interactive Reporting Map** | Clickable UK regional SVG map — click any of the 12 regions to see nearby cybercrime reporting centres with phone numbers, websites, and addresses. |
| **💬 AI Chatbot** | Floating chatbot widget powered by a local LLM (Ollama + Llama 3.2) with RAG grounding. Supports fullscreen mode (⛶) and pop-out to a new tab (↗). |
| **📊 Data-Driven Stats** | Animated counters and statistics on cyber threats, incidents, and response times. |
| **🌗 Dark / Light Theme** | Toggle between dark and light mode across the entire dashboard. |
| **🇲🇹 Malta Chatbot** | Separate Malta-specific interface (accessible from the landing page). |

---

## 🏗️ Architecture

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

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.8+ | Backend server and RAG pipeline |
| **pip** | Latest | Python package manager |
| **Ollama** | Latest | Local LLM inference engine |
| **Git** | Latest | Cloning the repository |
| **Modern Browser** | Chrome / Edge / Firefox | Frontend dashboard |

> [!IMPORTANT]
> Ollama must be installed and running with the `llama3.2` model pulled before starting the backend.

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Prantik-1811/Regional_Cybersec_Chatbot_UK_Malta.git
cd Regional_Cybersec_Chatbot_UK_Malta
```

### 2. Create a Python Virtual Environment

```bash
python -m venv .venv
```

**Activate it:**

- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Backend Dependencies

```bash
cd UK/backend
pip install -r requirements.txt
```

<details>
<summary>📦 Full dependency list</summary>

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.109.0 | Web framework (API server) |
| `uvicorn` | 0.27.0 | ASGI server |
| `httpx` | 0.26.0 | Async HTTP client |
| `beautifulsoup4` | 4.12.3 | HTML parsing for update checker |
| `chromadb` | 0.4.22 | Vector database for RAG |
| `sentence-transformers` | 2.2.2 | Text embeddings (`all-MiniLM-L6-v2`) |
| `langchain` | 0.1.0 | LLM orchestration framework |
| `langchain-ollama` | 0.0.2 | Ollama integration for LangChain |
| `pypdf2` | 3.0.1 | PDF text extraction |
| `pdfplumber` | 0.10.3 | Advanced PDF parsing |
| `python-dotenv` | 1.0.0 | Environment variable management |
| `aiofiles` | 23.2.1 | Async file operations |

</details>

### 4. Install & Configure Ollama

1. Download and install Ollama from [ollama.com](https://ollama.com/download).

2. Pull the LLM model:
   ```bash
   ollama pull llama3.2
   ```

3. Verify it's running:
   ```bash
   ollama list
   ```
   You should see `llama3.2` in the output.

> [!NOTE]
> Ollama runs by default on `http://localhost:11434`. If you need a different URL, update `OLLAMA_BASE_URL` in `UK/backend/.env`.

### 5. Ingest Data into the Vector Database

Before the chatbot can answer questions, you need to populate the ChromaDB vector store with the scraped data:

```bash
cd UK/backend
python ingest.py
```

This will:
- Read the scraped JSON data from `Scraped files/cyber_chatbot_UK1.json`
- Chunk and embed the documents using `all-MiniLM-L6-v2`
- Store the vectors in `UK/backend/chroma_db/`

---

## ▶️ Running the Application

### Option A: One-Click Launch (Windows)

Double-click **`run_chatbot.bat`** in the root directory.

This will:
1. Start the FastAPI backend server (port `8001`) in a new terminal window.
2. Wait 5 seconds for initialization.
3. Open the dashboard (`UK/index.html`) in your default browser.

### Option B: Manual Startup

**Step 1 — Start the backend server:**

```bash
cd UK/backend
python main.py
```

You should see:
```
Loaded collection with N chunks
Connected to Ollama at http://localhost:11434
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Step 2 — Open the frontend:**

Open `UK/index.html` directly in your browser (double-click the file or use `Ctrl+O` in the browser).

> [!TIP]
> The frontend works on the `file://` protocol — no local web server is needed. The chatbot communicates with the backend via `http://localhost:8001`.

---

## ✅ Verifying the Setup

After starting the application, verify everything is working:

| Check | How |
|-------|-----|
| **Backend is running** | Visit [http://localhost:8001](http://localhost:8001) — should return `{"status": "online", ...}` |
| **API docs are accessible** | Visit [http://localhost:8001/docs](http://localhost:8001/docs) — Swagger UI should load |
| **Health check** | Visit [http://localhost:8001/api/health](http://localhost:8001/api/health) — `rag_available` should be `true` |
| **Frontend loads** | Open `UK/index.html` — dashboard should render with animated stats |
| **Chatbot responds** | Click 💬, type a question, and verify a response is generated |
| **Map is clickable** | Go to "Report Centers" tab and click a UK region |

---

## 📂 Project Structure

```
Regional_Cybersec_Chatbot_UK_Malta/
├── UK/                          # Main UK Dashboard Application
│   ├── index.html               #   Frontend entry point (SPA)
│   ├── scripts/
│   │   ├── main.js              #   Dashboard logic, tabs, map, counters
│   │   └── chatbot.js           #   Chatbot widget, fullscreen, popout
│   ├── styles/
│   │   ├── main.css             #   Core styles, theme, chatbot, cards
│   │   └── cyber-map.css        #   Threat map animations
│   ├── assets/
│   │   ├── uk-map.svg           #   Interactive UK region map (with embedded click script)
│   │   └── world-map.svg        #   Global threat map base
│   └── backend/
│       ├── main.py              #   FastAPI server (API endpoints)
│       ├── rag.py               #   RAG pipeline (ChromaDB + Ollama)
│       ├── ingest.py            #   Data ingestion into vector DB
│       ├── update_checker.py    #   Checks sources for new content
│       ├── pdf_processor.py     #   PDF text extraction utilities
│       ├── train_chatbot.py     #   Training data preparation
│       ├── verify_chatbot.py    #   Backend verification script
│       ├── requirements.txt     #   Python dependencies
│       ├── .env                 #   Environment config (Ollama URL, paths)
│       └── chroma_db/           #   Vector database storage
│
├── Malta/                       # Malta Regional Chatbot
│   ├── index.html               #   Malta frontend
│   ├── Scripts/                 #   Malta-specific JS
│   └── Styles/                  #   Malta-specific CSS
│
├── Scraped files/               # Raw scraped JSON data
│   ├── cyber_chatbot_UK1.json   #   Primary UK data (used by backend)
│   ├── cyber_chatbot_UK2.json   #   Additional datasets
│   ├── cyber_chatbot_UK3.json
│   ├── cyber_chatbot_UK4.json
│   └── cyber_chatbot_UK_artic.json
│
├── Training_Data/               # Training datasets for RAG pipeline
├── tools/                       # Development utilities
│   ├── gather_data.py           #   Web scraping tool
│   ├── inspect_pdfs.py          #   PDF content inspector
│   ├── inspect_pdfs_v2.py       #   Improved PDF inspector
│   ├── debug_api.py             #   API debugging utility
│   └── debug_json.py            #   JSON data debugger
│
├── run_chatbot.bat              # One-click launcher (Windows)
├── README.md                    # This file
└── world.svg                    # Global map asset
```

---

## 🔌 API Reference

The backend exposes the following REST endpoints:

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/` | GET | Server status | — |
| `/api/health` | GET | Health check (RAG + Ollama status) | — |
| `/api/query` | POST | Chat with the AI | `{"query": "What is phishing?", "region": "UK"}` |
| `/api/updates` | GET | Check sources for new content | `?limit=5` |
| `/api/articles` | GET | Retrieve news articles | `?limit=10` |

Full interactive documentation is available at **[http://localhost:8001/docs](http://localhost:8001/docs)** when the server is running.

---

## ⚙️ Configuration

The backend is configured via environment variables in `UK/backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `JSON_DATA_PATH` | `../../Scraped files/cyber_chatbot_UK1.json` | Path to scraped JSON data |
| `CHROMA_DB_PATH` | `./chroma_db` | Path to ChromaDB vector store |

---

## 🛠️ Troubleshooting

<details>
<summary><strong>Chatbot says "I'm currently offline"</strong></summary>

The frontend can't reach the backend. Make sure:
1. The backend is running (`python main.py` in `UK/backend/`).
2. It's listening on port `8001`.
3. No firewall is blocking `localhost:8001`.
</details>

<details>
<summary><strong>Backend starts but RAG says "not initialized"</strong></summary>

The vector database is empty. Run the ingestion script:
```bash
cd UK/backend
python ingest.py
```
</details>

<details>
<summary><strong>"Error calling LLM: Connection refused"</strong></summary>

Ollama is not running. Start it:
```bash
ollama serve
```
Then verify the model is available:
```bash
ollama list
```
</details>

<details>
<summary><strong>Map regions are not clickable</strong></summary>

This can happen if the SVG doesn't load. Verify that `UK/assets/uk-map.svg` exists and the browser's console doesn't show errors. The map uses `postMessage` to communicate between the SVG and the parent page.
</details>

---

## 🤝 Data Sources & Partners

| Source | URL |
|--------|-----|
| National Cyber Security Centre (NCSC) | [ncsc.gov.uk](https://www.ncsc.gov.uk) |
| Action Fraud | [actionfraud.police.uk](https://www.actionfraud.police.uk) |
| Information Commissioner's Office (ICO) | [ico.org.uk](https://ico.org.uk) |
| GOV.UK Cyber Security | [gov.uk](https://www.gov.uk/government/topics/cyber-security) |

---

## 📄 License

This project is developed for the **Regional Cybersecurity Chatbot — UK & Malta** academic project.

---

*Built with FastAPI, ChromaDB, Ollama, and vanilla HTML/CSS/JS.*
