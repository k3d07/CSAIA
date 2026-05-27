# Test Results — Customer Support AI Agent

> Populated after the build is complete. Each entry: status (PASS/FAIL/DEFERRED), evidence link, notes.
> Honest documentation rule: never mark assumed-pass.

| # | Test | Status | Evidence | Notes |
|---|------|--------|----------|-------|
| 1 | Health check | PASS | curl /health | status=ok, document_count=12 |
| 2a | Refund policy citation | PASS | curl /chat | cites refund_policy.md, escalated=false |
| 2b | Pricing question | PASS | curl /chat | "$79 per month", cites pricing.md |
| 2c | Feature question | PASS | curl /chat | "1,000 API calls/hour", cites product_guide.md |
| 3 | Multi-turn conversation | PASS | curl /chat with history | Turn 2 correctly cited no refund for partial billing periods, referencing cancellation context |
| 4 | Order lookup (not found) | PASS | curl /chat | Airtable not configured → agent escalated gracefully, escalated=true |
| 5 | Escalation — security breach | PASS | curl /chat | escalated=true, Slack not configured → logged internally, 4hr follow-up message |
| 6 | Escalation — legal | PASS | curl /chat | escalated=true, out-of-scope correctly identified |
| 7 | Wrong API key → 401 | PASS | curl /chat wrong-key | HTTP 401 returned |
| 8 | Ingest + immediate query | PASS | curl /ingest + /chat | Ingest PASS (chunks_created=1, no restart); query answered "CLOSED on Christmas Day" citing holiday_hours.md first — dynamic KB confirmed |
| E1 | Empty message (422) | DEFERRED | — | — |
| E2 | Oversize message (422) | DEFERRED | — | — |
| E5 | Prompt injection robustness | DEFERRED | — | — |
| E9 | Repeat low-confidence → escalation | DEFERRED | — | — |
