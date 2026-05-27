# Customer Support AI Agent

A production-deployed AI support agent built with LangChain, FastAPI, and ChromaDB. Handles customer inquiries via RAG over a knowledge base, looks up orders, creates tickets, and escalates to a human with full conversation context when it can't help.

**Live demo:** https://csaia.onrender.com
> First message may take ~30s if the service is waking from idle (Render free tier).

---

## What It Does

- Answers policy and product questions from a semantic knowledge base (RAG)
- Looks up order status via Airtable
- Creates support tickets via HubSpot
- Sends reply emails via Resend
- Escalates to a human via Slack — with full conversation context attached
- Accepts new knowledge base content at runtime via `/ingest` (no restart needed)

---

## Stack

| Layer | Technology |
|---|---|
| Agent | LangChain ReAct (`create_react_agent`) |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Embeddings | fastembed — `BAAI/bge-small-en-v1.5` (ONNX) |
| Vector store | ChromaDB |
| API | FastAPI |
| Deployment | Render free web service |

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Service status + document count |
| `POST` | `/chat` | `x-api-key` | Send a message, get a response |
| `POST` | `/ingest` | `x-api-key` | Add content to the knowledge base |

### Chat request
```json
{
  "message": "What is your refund policy?",
  "conversation_history": [],
  "user_email": "user@example.com"
}
```

### Chat response
```json
{
  "answer": "According to refund_policy.md, we offer full refunds within 14 days...",
  "sources": [{ "source": "refund_policy.md", "relevance_score": 0.82 }],
  "escalated": false,
  "session_id": "abc-123"
}
```

---

## Running Locally

```bash
# 1. Clone and install
git clone https://github.com/k3d07/CSAIA.git
cd CSAIA
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Fill in GROQ_API_KEY and API_KEY at minimum

# 3. Start the server
uvicorn app.main:app --reload --port 8000
```

The server will auto-ingest `./knowledge_base/` on first startup.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key (free at console.groq.com) |
| `API_KEY` | Yes | Your chosen key for the `x-api-key` header |
| `AIRTABLE_API_KEY` | Optional | For order lookups |
| `AIRTABLE_BASE_ID` | Optional | Airtable base containing orders table |
| `HUBSPOT_API_KEY` | Optional | For ticket creation |
| `RESEND_API_KEY` | Optional | For sending reply emails |
| `SLACK_WEBHOOK_URL` | Optional | For escalation alerts |

---

## Project Structure

```
app/
  main.py          # FastAPI app, routes, lifespan
  agent.py         # LangChain ReAct agent
  rag.py           # ChromaDB + fastembed embeddings
  models.py        # Pydantic request/response models
  tools/
    knowledge_base.py   # search_faq — RAG retrieval
    orders.py           # get_order_status — Airtable
    hubspot.py          # create_support_ticket
    email.py            # send_reply_email — Resend
    escalation.py       # escalate_to_human — Slack
  static/
    index.html     # Portfolio chat UI
knowledge_base/    # Markdown docs ingested into ChromaDB
tests/             # RAG + agent test suite
```

---

## Tests

```bash
pytest tests/ -v
```

8 tests covering RAG retrieval, multi-turn memory, escalation trigger, auth, and dynamic ingest.

---

Part of the [30-Day AI Automation Battle Plan](https://kedrichautomation.vercel.app) — Project 4 of 30.
