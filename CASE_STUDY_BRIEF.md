# Case Study: Customer Support AI Agent (CSAIA)
**Project 4 of 30 — Kedrich Custodio | kedrichautomation.vercel.app**

---

## Overview

A production-deployed AI support agent that handles customer inquiries, looks up orders, creates tickets, and escalates to a human with full context — automatically. Built in one session as part of a 30-day AI automation portfolio challenge.

**Live demo:** https://csaia.onrender.com
**Source code:** https://github.com/k3d07/CSAIA

---

## The Problem

Most AI chatbots fail in one of two ways: they either make up answers when they don't know something, or they dump the customer into a generic "contact support" dead end with no context. Neither is acceptable in a real support workflow.

The goal was to build something that behaves like a real Tier-1 support agent — answers from documentation when it can, looks up real account data, and when it hits a wall, escalates with full conversation context so a human agent can actually pick up where it left off.

---

## What It Does

| Capability | How |
|---|---|
| Answers policy/product questions | RAG over ChromaDB knowledge base |
| Looks up order status | Airtable API |
| Creates support tickets | HubSpot API |
| Sends reply emails | Resend API |
| Escalates with full context | Slack webhook + conversation history |
| Accepts new knowledge without restart | `/ingest` API endpoint |

---

## Stack

| Layer | Technology |
|---|---|
| Agent framework | LangChain (ReAct pattern) |
| LLM | Groq — `llama-3.3-70b-versatile` |
| Embeddings | fastembed — `BAAI/bge-small-en-v1.5` (ONNX, no PyTorch) |
| Vector store | ChromaDB (cosine similarity) |
| API | FastAPI + Uvicorn |
| Deployment | Render free web service |

---

## Key Engineering Decisions

### 1. ReAct agent instead of tool-calling agent

The original plan used LangChain's `create_tool_calling_agent`, which routes tool calls through the model's native function-calling API. On Groq, this fails — Groq models emit tool calls in an XML format that Groq's own API then rejects at validation.

Switched to `create_react_agent` (text-based Thought/Action/Observation loop). This completely bypasses Groq's tool-call API, works reliably across all models, and produces readable reasoning traces visible in the logs.

### 2. fastembed instead of sentence-transformers

Render's free tier has 512MB RAM. `sentence-transformers` pulls in PyTorch (~1.5GB), which causes an OOM kill during startup. Swapped to `fastembed`, which uses ONNX Runtime — the same model quality at ~130MB total footprint.

Also bypassed `langchain_community.embeddings.FastEmbedEmbeddings` entirely — its Pydantic `PrivateAttr` for `_model` initializes as `None` on Render due to a class-level initialization order issue. Wrote a direct wrapper class instead:

```python
class LocalFastEmbeddings(Embeddings):
    def __init__(self, model_name, cache_dir):
        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)

    def embed_documents(self, texts):
        return [e.tolist() for e in self._model.embed(texts)]

    def embed_query(self, text):
        return list(self._model.embed([text]))[0].tolist()
```

The `.tolist()` call is critical — `list(numpy_array)` produces `numpy.float32` values, which ChromaDB rejects. `.tolist()` converts to native Python floats.

### 3. Escalation with full context

The `escalate_to_human` tool takes both a `reason` and an optional `conversation_context` string. When the agent fires it, it passes the full conversation history — so the human agent receiving the Slack alert knows exactly what was already tried. This is the differentiator vs. a basic chatbot.

### 4. Zero-downtime knowledge base updates

The `/ingest` endpoint accepts raw text or document content and adds it to ChromaDB without a server restart. The lifespan hook auto-ingests `./knowledge_base/` on startup if the vector store is empty, so every deploy starts with a populated index.

---

## Challenges

**Render Python version conflict:** `langchain-chroma 0.2.4` requires `numpy>=2.1.0` on Python 3.13+, but `langchain 0.3.0` pins `numpy<2.0.0`. The conflict made the build fail silently on Render's default Python 3.14. Fixed by pinning `PYTHON_VERSION=3.12.10` as an environment variable in the Render dashboard.

**Model pre-download:** fastembed downloads the ONNX model on first use. On Render, this hit the 30s request timeout on cold starts. Fixed by adding the model download to the build command so the binary is baked into the deployed image.

**Groq rate limits:** The free Groq tier has a 100k tokens/day limit. Hit it during testing. Resolved by using a second Groq account for testing and reserving the primary key for the deployed service.

---

## Results

- 8/8 tests passing (RAG retrieval, multi-turn memory, escalation, auth, dynamic ingest)
- Deployed and live on Render free tier
- Cold start: ~30s after idle spin-down (Render free tier behavior, documented in UI)
- Active: responses in 2–5s
- Knowledge base: 12 chunks across 5 policy documents
- Zero paid API calls — Groq, fastembed, and ChromaDB are all free tier

---

## Screenshots

| | |
|---|---|
| ![Chat UI](case-study-assets/01-chat-ui-idle.png) | ![RAG Answer](case-study-assets/02-rag-answer-refund.png) |
| *Portfolio-themed chat interface* | *RAG answer citing source document* |
| ![Multi-turn](case-study-assets/03-multi-turn-shipping.png) | ![Escalation](case-study-assets/05-escalation-legal.png) |
| *Multi-turn conversation with source attribution* | *Automatic escalation on high-risk input* |

---

## What I'd Do Differently at Scale

- **Persistent disk on Render** — the free tier has an ephemeral filesystem, so ChromaDB is re-populated on every deploy. A paid tier with a mounted disk (or switching to a hosted vector DB like Pinecone) would fix this.
- **Streaming responses** — the current `/chat` endpoint waits for the full agent chain to complete before responding. Server-sent events would make the UI feel faster.
- **Relevance threshold tuning** — the 0.4 cosine threshold works for clean policy questions but escalates edge cases that a more tuned threshold would handle. A feedback loop to adjust this over time would help.
- **Slack webhook** — the free Slack webhook URL expired during testing (302 redirect to api.slack.com). In production this would use the Slack Events API with a proper OAuth app.
