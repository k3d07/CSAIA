# CLAUDE.md — Customer Support AI Agent

## Project Identity
**Name:** Customer Support AI Agent (CSAIA)
**Stack (as specified):** LangChain + FastAPI + ChromaDB + OpenAI GPT-4o
**Source of truth:** [Project4_Customer_Support_AI_Agent_Build_Guide.md](Project4_Customer_Support_AI_Agent_Build_Guide.md)
**Day:** Project 4 of 30-Day AI Automation Battle Plan
**Portfolio target:** kedrichautomation.vercel.app case study

## What This Is
A FastAPI service exposing 4 endpoints (`/chat`, `/escalate`, `/ingest`, `/health`) backed by a LangChain tool-calling agent with 5 tools:
1. `search_faq` — RAG over ChromaDB (semantic search of company docs)
2. `get_order_status` — Airtable lookup
3. `create_support_ticket` — HubSpot API
4. `send_reply_email` — Resend API
5. `escalate_to_human` — Slack webhook with full context

**The portfolio-critical feature:** the agent escalates with full context when it doesn't know — that's the differentiator vs. a toy chatbot.

## Key Decisions From Source File
- **Embedding model:** ~~`text-embedding-3-small`~~ → **`sentence-transformers/all-MiniLM-L6-v2`** (free-tier swap, local, 384-dim)
- **LLM:** ~~`gpt-4o`~~ → **`llama-3.3-70b-versatile` via Groq**, temperature=0 (free-tier swap)
- **Chunking:** RecursiveCharacterTextSplitter, chunk_size=1000, overlap=200
- **Retrieval:** top-k=4, relevance threshold 0.4 (below → escalate)
- **Agent:** `create_tool_calling_agent` + AgentExecutor, max_iterations=6, handle_parsing_errors=True
- **Auth:** API key via `x-api-key` header on `/chat` and `/ingest`
- **Vector store persistence:** `./db` (gitignored)
- **Knowledge base source:** `./knowledge_base/*.md` (5 docs for fake company "NovaTech Solutions")
- **Dynamic ingestion:** `/ingest` endpoint adds docs without server restart
- **Lifespan hook:** auto-ingests `./knowledge_base/` on startup if vector store empty

## Free-Tier Constraints (User Rule)
No credit card. If a service requires billing, swap to a free alternative and document the swap as a project-decision memory.

**Known billing blockers in the source file:**
- ~~**OpenAI**~~ → **RESOLVED:** Groq (LLM) + HuggingFace local embeddings. See memory `decision_openai_swap_resolved`.
- ~~**Railway**~~ → **RESOLVED:** Render free web service. See memory `decision_railway_swap_resolved`.
- **HubSpot, Slack, Resend, Airtable** — usable on free tiers.

## Working Style Rules
- One section at a time. Never advance until user says `next`.
- Exact configs, exact field values. No vague instructions.
- If a value isn't in the source file or context files, **ask before assuming**.
- User has coding + cybersecurity background — skip basics.
- Screenshot-first debugging: identify what's wrong, give click-by-click fixes.
- Real engineering decisions → save as project-decision memory + link from MEMORY.md.
- After each section: update this status block AND check off in [progress/checklist.md](progress/checklist.md).

## Status Block

**Current section:** Step 7 — Run Locally (not started)
**Last completed:** Step 6 — FastAPI app (`app/main.py`) with 4 routes, auth, lifespan
**Blocked on:** Need `.env` filled in (at minimum `GROQ_API_KEY` + `API_KEY`) before first run
**Next action:** Create `.env` from `.env.example`, fill in keys, run `uvicorn app.main:app --reload --port 8000`

### Section Progress
- [x] Scaffolding (folders, configs, docs split, memory)
- [x] Step 0a — OpenAI swap resolved (Groq llama-3.3-70b-versatile + HF MiniLM-L6-v2)
- [x] Step 0b — Railway swap resolved (Render free web service)
- [x] Step 1 — Knowledge base documents
- [x] Step 2 — Pydantic models
- [x] Step 3 — RAG pipeline (with cosine distance fix for HF embeddings)
- [x] Step 4 — Five tools
- [x] Step 5 — LangChain agent (Groq, tool-calling, source extraction)
- [x] Step 6 — FastAPI app (4 routes, auth, lifespan auto-ingest)
- [ ] Step 1 — Create knowledge base documents
- [ ] Step 2 — Pydantic models
- [ ] Step 3 — RAG pipeline + isolation test
- [ ] Step 4 — Five tools
- [ ] Step 5 — LangChain agent
- [ ] Step 6 — FastAPI app
- [ ] Step 7 — Run locally
- [ ] Step 8 — Test suite (8 tests)
- [ ] Step 9 — Deploy
- [ ] Post-build — test-results, case-study assets, CASE_STUDY_BRIEF

## File Map
- `app/` — application code
- `knowledge_base/` — fake NovaTech docs (RAG corpus)
- `db/` — ChromaDB persistence (gitignored)
- `tests/` — RAG + agent tests
- `docs/` — source file split by section
- `context/` — architecture, credentials template
- `progress/` — checklist
- `sample-data/` — test payloads, mock Airtable rows
- `test-results/` — manual test logs (populated post-build)
- `case-study-assets/` — screenshots, scrubbed workflow exports
