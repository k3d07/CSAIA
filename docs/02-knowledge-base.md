# 02 — Step 1: Create the Fake Knowledge Base

Source: lines 172–428 of source file.

This is not a throwaway step. Thin docs → bad demo. Realistic, detailed content → good retrieval scores → portfolio-worthy demo.

Fake company: **NovaTech Solutions** (B2B SaaS).

Five files go in `knowledge_base/`:

- `faq.md` — Account & Billing, Tech Support, Features
- `refund_policy.md` — 14-day window, exceptions, partial, disputes
- `shipping_policy.md` — digital delivery only
- `product_guide.md` — Starter / Pro / Enterprise tiers, features
- `pricing.md` — pricing table, add-ons, discounts, guarantees

The full content for all five is in the source file (lines 178–428). Implementation step: copy each verbatim from the source, expand if you want richer demo coverage.

## Pricing Table (snippet for quick reference)

| Plan | Monthly | Annual (save 20%) |
|------|---------|-------------------|
| Starter | $29/mo | $278/yr ($23.17/mo) |
| Pro | $79/mo | $758/yr ($63.17/mo) |
| Enterprise | Custom | Custom |

## Key Numbers Used in Tests
- Refund window: **14 days** full refund.
- Annual refund: prorated between days 30–180 minus 10% fee. None after 180.
- Pro plan: **$79/mo**, 10,000 API calls/hour, 15 team members, 50 GB storage, 12hr SLA.
- Starter plan: **$29/mo**, 1,000 API calls/hour, 3 team members, 5 GB.
- Failed payment: 3 retries over 7 days, then suspension.
