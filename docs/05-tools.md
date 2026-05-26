# 05 — Step 4: The Five Tools

Source: lines 695–1019 of source file. Each tool lives in its own file under `app/tools/`.

> The docstring on each `@tool` is **not decoration** — it's the description the LLM reads to decide when to call the tool. Write precisely.

## 1. `app/tools/knowledge_base.py` — search_faq

Wraps `app.rag.search_knowledge_base`. Returns top-4 formatted with source + relevance score. **Tells the LLM**: "Use FIRST for any customer question. If no scores above 0.4, escalate."

```python
@tool
def search_faq(query: str) -> str:
    """Search the company's knowledge base..."""
    results = _search(query, k=4)
    if not results:
        return "No relevant information found in the knowledge base."
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"[Result {i}] Source: {r['source']} (relevance: {r['relevance_score']})\n"
            f"{r['content']}"
        )
    return "\n\n---\n\n".join(formatted)
```

## 2. `app/tools/orders.py` — get_order_status

Calls Airtable: `GET https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?filterByFormula={OrderID}='<id>'`. Graceful fallback if no Airtable config. Returns Status, OrderDate, Product, EstimatedDelivery, TrackingNumber.

## 3. `app/tools/hubspot.py` — create_support_ticket

`POST https://api.hubapi.com/crm/v3/objects/tickets` with payload:
```json
{
  "properties": {
    "subject": "Support Request — <customer_email>",
    "content": "<issue_summary>",
    "hs_ticket_priority": "MEDIUM",
    "hs_pipeline": "0",
    "hs_pipeline_stage": "1"
  }
}
```

## 4. `app/tools/email.py` — send_reply_email

Uses `resend` SDK: `resend.Emails.send({"from": FROM_EMAIL, "to": ..., "subject": ..., "text": ...})`.
**`FROM_EMAIL = "support@yourdomain.com"`** — must change to a verified Resend domain or sandbox `onboarding@resend.dev`.

## 5. `app/tools/escalation.py` — escalate_to_human

Posts Slack Block Kit message:
- header: "🚨 Support Escalation Required"
- section: Reason
- section: Conversation Context (truncated to 1500 chars, in code block)
- context footer: "AI support agent could not resolve. Human follow-up needed within 2 hours."

Returns customer-facing message: "...will contact you within 2 business hours. You don't need to repeat yourself."

## Universal Pattern: Graceful Degradation

Every tool checks for missing API keys and returns a graceful fallback string instead of raising. The agent reads that string and decides what to do (often: escalate). This means partial-config demos still run end-to-end.
