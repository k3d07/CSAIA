# context/project.md — Architecture, Configs, Data Map

## High-Level Architecture

```
                      ┌───────────────────────┐
       client ──────► │  FastAPI (app/main.py)│
                      └──────────┬────────────┘
                                 │ verify_api_key (x-api-key)
                                 ▼
                      ┌───────────────────────┐
                      │  run_agent (agent.py) │
                      │  AgentExecutor + LLM  │
                      └──────────┬────────────┘
                                 │ tool calls
       ┌─────────────┬───────────┼───────────┬─────────────┐
       ▼             ▼           ▼           ▼             ▼
   search_faq   get_order   create_     send_reply   escalate_
   (ChromaDB)   _status     support_    _email       to_human
                (Airtable)  ticket      (Resend)     (Slack)
                            (HubSpot)
```

On startup, FastAPI's lifespan hook checks the vector store. If empty, it ingests `./knowledge_base/*.md` via `app/rag.py::ingest_directory`.

## Component Configs

### Embeddings (swapped from OpenAI → HuggingFace local)
- Model: `sentence-transformers/all-MiniLM-L6-v2` (env: `HF_EMBEDDING_MODEL`)
- Provider: local, via `langchain-huggingface` + `sentence-transformers`
- Dimensions: 384
- No API key, no rate limit, weights cached to disk on first run (~80 MB)

### LLM (swapped from OpenAI → Groq)
- Model: `llama-3.3-70b-versatile` (env: `GROQ_MODEL`)
- temperature: 0
- Provider: Groq Cloud (free tier, native function-calling)
- Env: `GROQ_API_KEY`

### Vector Store (ChromaDB)
- Collection: `support_knowledge_base`
- Persist dir: `./db` (env: `CHROMA_PERSIST_DIR`)
- Distance: cosine (chroma default)

### Text Splitter
- `RecursiveCharacterTextSplitter`
- chunk_size: 1000
- chunk_overlap: 200
- separators: `["\n\n", "\n", ".", "!", "?", " "]`

### Retrieval
- Top-k: 4
- Confidence threshold: 0.4 (relevance score below this → escalate)
- Returns: `[{content, source, relevance_score}]`

### Agent
- `create_tool_calling_agent(llm, tools, prompt)`
- `AgentExecutor(verbose=True, max_iterations=6, handle_parsing_errors=True)`
- ChatPromptTemplate with system prompt + chat_history placeholder + input + agent_scratchpad

### API Auth
- Header: `x-api-key`
- Env: `API_KEY`
- Returns 401 on mismatch
- Applied to: `/chat`, `/ingest`. Not `/health` or `/`.

### CORS
- `allow_origins=["*"]` (dev). Restrict in production.

## Tool Specs (LLM-Visible Behavior)

| Tool | Inputs | Returns | When LLM should call |
|------|--------|---------|----------------------|
| `search_faq` | query: str | formatted excerpts with source + score | FIRST for any product/policy question |
| `get_order_status` | order_id: str | status block or "not found" | customer mentions order ID |
| `create_support_ticket` | issue_summary, customer_email | ticket ID + confirmation | complex issue needing human follow-up |
| `send_reply_email` | to_email, subject, body | message ID confirmation | resolved issue + email follow-up valuable |
| `escalate_to_human` | reason, conversation_context | customer-facing escalation message | low confidence, fraud/legal, explicit request, frustration |

## Data Map

### Knowledge Base (RAG corpus)
Lives in `./knowledge_base/*.md`. Fake company: **NovaTech Solutions** (B2B SaaS).
- `faq.md` — Account & Billing, Tech Support, Features
- `refund_policy.md` — 14-day, exceptions, partial, disputes
- `shipping_policy.md` — digital delivery (no physical shipping)
- `product_guide.md` — Starter / Pro / Enterprise plan details
- `pricing.md` — pricing table, add-ons, discounts, guarantees

### Airtable (Orders)
- Base: `AIRTABLE_BASE_ID`
- Table: `Orders` (env override: `AIRTABLE_TABLE_NAME`)
- Filter: `{OrderID} = '<id>'`
- Expected fields: `OrderID`, `Status`, `OrderDate`, `Product`, `EstimatedDelivery`, `TrackingNumber`

### HubSpot (Tickets)
- Endpoint: `POST https://api.hubapi.com/crm/v3/objects/tickets`
- Pipeline: `0` (default support), stage: `1` (New)
- Priority: `MEDIUM`
- Subject format: `Support Request — <customer_email>`

### Resend (Email)
- From: `support@yourdomain.com` (must be verified domain — replace at config time)
- `resend.Emails.send({from, to, subject, text})`

### Slack (Escalation)
- Webhook URL (env: `SLACK_WEBHOOK_URL`)
- Block kit: header + section (reason) + section (context, truncated 1500 chars) + context footer

## Pydantic Models (request/response shapes)

`ChatRequest`: `{message: str, conversation_history: list[Message]=[], user_email?: str, session_id?: str}`
`ChatResponse`: `{answer: str, sources: list[Source], escalated: bool, session_id?: str, timestamp: str}`
`Source`: `{document: str, excerpt: str}`
`IngestRequest`: `{content: str, document_name: str, metadata?: dict}`
`IngestResponse`: `{status: str, document_name: str, chunks_created: int}`
`HealthResponse`: `{status: str, document_count: int, timestamp: str}`

## Environment Variables
See `context/credentials.md` for the template the user must fill in.

## Deferred Decisions (must resolve before that section)
- ~~Step 0a — OpenAI replacement~~ **RESOLVED** → Groq (LLM) + HuggingFace local embeddings. See [memory/decision_openai_swap_resolved.md].
- ~~Step 0b — Railway replacement~~ **RESOLVED** → Render free web service. See [memory/decision_railway_swap_resolved.md].
- **Resend FROM domain** — `support@yourdomain.com` placeholder; need a verified Resend domain or use Resend's sandbox `onboarding@resend.dev`.
