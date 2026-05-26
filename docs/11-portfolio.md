# 11 — Portfolio Materials (README, Loom, Upwork)

Source: lines 1591–1740 of source file.

## README.md Structure (from source)
- Title: Customer Support AI Agent — LangChain + FastAPI + ChromaDB + OpenAI GPT-4o
- The Problem (60–70% framing)
- The Solution (LangChain + RAG + citations + escalation with context)
- How It Works (numbered flow)
- Endpoints table
- Stack list
- Key Features (RAG citations, dynamic KB, graceful escalation, multi-turn memory, API auth, live URL)
- Setup → docs/setup.md
- Live Demo: [URL]
- Loom Walkthrough: [link]

## Loom Script (6–8 min)

| Time | Beat |
|------|------|
| 0:00–0:45 | The problem — chatbots that confidently bullshit. This one (a) only answers from verified docs (b) knows when to stop and get a human. |
| 0:45–2:00 | Show file structure. Five tools. LangChain orchestrates. FastAPI serves. ChromaDB stores embeddings. |
| 2:00–4:00 | Happy path: refund question, pricing question. Show sources cited. |
| 4:00–5:30 | Escalation: security breach question. Show Slack alert with full context. Show customer-facing response. |
| 5:30–6:30 | Ingest demo: hit `/ingest` with new doc, immediately query it. Searchable instantly, no restart. |
| 6:30–7:30 | Show `tools/escalation.py` and `rag.py` relevance threshold. |
| 7:30–8:00 | Close: Railway URL (or swap), GitHub link. KB is a config change, not a rebuild. |

## Upwork Portfolio Description (verbatim ready-to-paste)

```
Customer Support AI Agent | LangChain + FastAPI + ChromaDB + OpenAI

Built a production-grade AI support agent that answers customer
questions from a company knowledge base with cited sources.
Uses RAG (Retrieval-Augmented Generation) over ChromaDB —
every answer is retrieved from real documents, not hallucinated.

Five tools: knowledge base search, order lookup (Airtable),
HubSpot ticket creation, email via Resend, and smart escalation
to human agents via Slack with full conversation context.

The escalation logic is the key differentiator: the agent knows
what it doesn't know. Low-confidence answers, security issues,
and legal matters route to human agents with everything they need
to take over — no context lost, no customer asked to repeat.

Deployed on Railway. Dynamic knowledge base — new documents
ingested via API without restarting.

Stack: LangChain, FastAPI, ChromaDB, OpenAI, HubSpot, Resend, Slack
[GitHub] [Live Demo] [Loom]
```
