# 00 — Overview & Business Framing

Source: lines 1–40 of Project4_Customer_Support_AI_Agent_Build_Guide.md

## What's Different About This Project
- Pure Python — no Make / n8n / drag-and-drop. Real project structure, dependency management, async code, deployed API.
- Introduces **RAG** — retrieval-augmented generation. The LLM retrieves chunks from your actual documents and answers from those, with citations. That's what makes it production-worthy.

## Business Framing
Support teams spend 60–70% of their time answering questions already in the docs. This agent handles those automatically with cited sources. Anything it can't answer confidently is escalated to a human with full context — no ticket dropped.

## The Build — Four Endpoints
- `POST /chat` — main endpoint. User message + history in, answer + sources out.
- `POST /escalate` — auto-called when confidence is low. Creates HubSpot ticket + Slack alert.
- `POST /ingest` — accept document text or file uploads, add to ChromaDB without restart.
- `GET /health` — uptime + vector store doc count.

## The Five Tools
1. `search_knowledge_base(query)` — semantic search over ChromaDB, top-4 chunks + source names
2. `get_order_status(order_id)` — fake Airtable orders DB (simulates CRM/ERP)
3. `create_support_ticket(issue, email)` — HubSpot API
4. `send_reply_email(to, subject, body)` — Resend API
5. `escalate_to_human(reason, context)` — Slack alert with full context

> Escalation is the portfolio-critical tool. Any system can answer easy questions. A system that knows what it doesn't know — and hands off gracefully with full context — is what a real business would trust.
