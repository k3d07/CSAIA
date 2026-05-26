# 01 — Project Structure & Environment Setup

Source: lines 42–168 of source file.

## Project Structure (from guide)

```
customer-support-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, route definitions
│   ├── agent.py             ← LangChain agent setup, tool definitions
│   ├── rag.py               ← ChromaDB vector store, ingestion, retrieval
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   ├── orders.py
│   │   ├── hubspot.py
│   │   ├── email.py
│   │   └── escalation.py
│   └── models.py            ← Pydantic request/response models
├── knowledge_base/          ← fake company docs
├── db/                      ← ChromaDB persists here (gitignored)
├── tests/
│   └── test_agent.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

> **Note on layout:** In this repo we flattened — the `customer-support-agent/` wrapper is the repo root itself.

## Virtual Environment

```powershell
# Windows PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
python -m venv venv
source venv/bin/activate
```

## requirements.txt

```
# Core
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.7.0
python-dotenv==1.0.1
httpx==0.27.0

# LangChain
langchain==0.3.0
langchain-openai==0.2.0
langchain-community==0.3.0
langchain-chroma==0.1.4

# Vector store
chromadb==0.5.5

# Document loading
pypdf==4.3.1
unstructured==0.15.0

# APIs
openai==1.40.0
resend==2.3.0

# Utils
python-multipart==0.0.9
aiofiles==23.2.1
```

Install: `pip install -r requirements.txt`

## .env Template

```
OPENAI_API_KEY=sk-...
HUBSPOT_API_KEY=pat-na1-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
RESEND_API_KEY=re_...
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
AIRTABLE_TABLE_NAME=Orders
API_KEY=your-secret-api-key-for-this-service
CHROMA_PERSIST_DIR=./db
```

`.env.example` mirrors this with placeholders. Commit `.env.example`, never `.env`.

## .gitignore (from guide)

```
venv/
__pycache__/
*.pyc
.env
db/
*.egg-info/
.DS_Store
```

Our project's `.gitignore` extends this with `.venv/`, `.env.*` allowlisting, `context/credentials.md`, `.pytest_cache/`, IDE dirs, and case-study WIP exclusions.
