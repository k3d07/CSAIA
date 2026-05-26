# Master Checklist

## Structure and Setup
- [x] Project directory structure created
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt
- [ ] .env populated with all keys
- [x] .env.example committed (no real keys)
- [x] .gitignore includes venv/, db/, .env

## Step 0 — Free-Tier Swap Decisions
- [x] OpenAI swap → Groq (`llama-3.3-70b-versatile`) + HF local embeddings (`all-MiniLM-L6-v2`)
- [x] Railway swap → Render free web service (Procfile-compatible, GitHub-connected)
- [ ] Resend FROM domain decided (sandbox vs verified domain)

## Knowledge Base (Step 1)
- [x] faq.md created
- [x] refund_policy.md created
- [x] shipping_policy.md created
- [x] product_guide.md created
- [x] pricing.md created
- [x] All 5 markdown documents have realistic content (verbatim from source guide)

## Models (Step 2)
- [x] app/models.py — all Pydantic classes defined

## RAG Pipeline (Step 3)
- [ ] app/rag.py — embeddings + vector store + ingest + search
- [ ] tests/test_rag.py written
- [ ] Test script runs clean
- [ ] All test queries return results with scores above 0.4
- [ ] Chunks count between 40–70

## Tools (Step 4)
- [x] knowledge_base.py — search_faq with precise docstring
- [x] orders.py — get_order_status with Airtable + graceful fallback
- [x] hubspot.py — create_support_ticket with graceful fallback
- [x] email.py — send_reply_email with graceful fallback (FROM defaults to Resend sandbox)
- [x] escalation.py — escalate_to_human Slack block kit

## Agent (Step 5)
- [x] app/agent.py — TOOLS registry, LLM (Groq), SYSTEM_PROMPT
- [x] create_tool_calling_agent + AgentExecutor wired (max_iterations=6, return_intermediate_steps=True)
- [x] convert_history maps message formats correctly
- [x] run_agent extracts sources from intermediate_steps
- [x] escalated flag set when escalate_to_human fires

## API (Step 6)
- [x] app/main.py — FastAPI app, CORS, lifespan
- [x] verify_api_key dependency works (401 on bad key) — to validate in Step 7
- [x] /health returns document_count
- [x] /chat returns answer + sources + escalated + session_id
- [x] /ingest adds content and returns chunk count
- [x] Lifespan auto-ingests knowledge_base on first start

## Run Locally (Step 7)
- [ ] `uvicorn app.main:app --reload --port 8000` starts clean
- [ ] http://localhost:8000/docs loads
- [ ] Startup log shows chunk count

## Testing (Step 8) — Map to test-results/test-results.md
- [ ] Test 1: /health 200 + document_count > 0
- [ ] Test 2: Refund question → cited from refund_policy.md
- [ ] Test 3: Multi-turn conversation context preserved
- [ ] Test 4: Order lookup handles "not found" gracefully
- [ ] Test 5: Security/fraud → escalation + Slack alert (PORTFOLIO-CRITICAL)
- [ ] Test 6: Legal question → escalates
- [ ] Test 7: Wrong API key → 401
- [ ] Test 8: /ingest + immediate query without restart
- [ ] 10+ scenarios total (target) + edge cases logged

## Deployment (Step 9)
- [ ] Procfile created (or platform-equivalent)
- [ ] Deployed to Render free web service
- [ ] Env vars set in dashboard
- [ ] Live URL tested with same curl commands

## Documentation / Portfolio
- [ ] README complete
- [ ] Screenshots into case-study-assets/
- [ ] Workflow / repo exported, credentials scrubbed
- [ ] Loom recorded (6–8 min) — script in docs/10-portfolio.md
- [ ] CASE_STUDY_BRIEF.md generated
- [ ] requirements.txt committed
- [ ] .env.example committed
