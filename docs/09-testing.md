# 09 — Step 8: Testing (8 Core Tests)

Source: lines 1385–1568. Map results → `test-results/test-results.md`.

## Setup
```bash
export API_KEY="dev-key"   # PowerShell: $env:API_KEY = "dev-key"
```

## Test 1 — Health Check
```bash
curl http://localhost:8000/health
```
Expect: `{"status":"ok", "document_count": >0, "timestamp": "..."}`

## Test 2 — Knowledge Base (Happy Path)

Refund:
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -H "x-api-key: $API_KEY" \
  -d '{"message":"What is your refund policy?","user_email":"test@example.com"}'
```
Expect: cites `refund_policy.md`, escalated=false.

Pricing: "How much does the Pro plan cost per month?" → $79/mo, cites `pricing.md`.
Feature: "Does the Starter plan support API access?" → yes, 1,000 req/hr, cites `product_guide.md` or `faq.md`.

## Test 3 — Multi-turn Conversation
Turn 1: "I want to cancel my subscription."
Turn 2 (with conversation_history): "Will I get a refund for the remaining days?"
Expect: agent uses prior context (cancellation) when answering refund question.

## Test 4 — Order Lookup
"Can you check the status of my order ORD-2024-8821?" → calls `get_order_status`, returns "not found" gracefully (don't hallucinate, don't crash).

## Test 5 — Escalation (PORTFOLIO-CRITICAL)
"I think someone has unauthorized access to my account..." → calls `escalate_to_human`, posts Slack alert, returns confirmation. `escalated == true`. **Screenshot this + the Slack message.**

## Test 6 — Out-of-Scope (Legal)
"I want to sue your company for negligence..." → escalates.

## Test 7 — Wrong API Key
`-H "x-api-key: wrong-key"` → 401 Unauthorized.

## Test 8 — Ingest + Immediate Query
`POST /ingest` with `holiday_hours.md` content about Dec 25 / Jan 1 closures, then `POST /chat` with "Are you available on Christmas Day?" → answers from new doc, no restart. **This shows the dynamic KB selling point.**

## Honest Documentation Rule
If a test isn't run, mark it **deferred** in test-results — never assumed-pass.
