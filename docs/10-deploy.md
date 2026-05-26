# 10 — Step 9: Deploy

Source: lines 1571–1587 of source file.

## Original Guide: Railway

```bash
echo "web: uvicorn app.main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

Then push to GitHub → railway.app → New Project → Deploy from GitHub repo → add env vars → done.

## ⚠️ Free-Tier Blocker

**Railway removed its free tier in August 2023.** Now $5/month minimum (Trial doesn't count for permanent deployments). This conflicts with the project's "no card down" constraint.

## Candidate Swaps (decision deferred to this section)

| Platform | Free tier | Procfile? | Notes |
|----------|-----------|-----------|-------|
| **Render** | Yes — 1 free web service, spins down after 15 min idle | Yes (or `render.yaml`) | Easy. Cold start latency on first hit. |
| **Fly.io** | Free allowance (3 shared-cpu VMs) | `fly.toml` instead | Requires `flyctl` CLI. |
| **HuggingFace Spaces** | Yes (CPU) | `Dockerfile` | Public by default; private requires Pro. |
| **Replit Deployments** | Removed free deployments | — | Skip. |
| **Vercel** | Serverless functions only | — | Bad fit for FastAPI + ChromaDB persistence. |

**Recommendation:** Render. Document the swap as a project-decision memory when we reach Step 9.

## Deployment Caveat: ChromaDB Persistence

`./db` is local disk. On Render free tier, disks are ephemeral — the vector store resets on every redeploy. Mitigations:
- Re-run ingestion on every startup (current lifespan code already does this if empty). Adds ~30s cold start.
- Or use Render disks (paid) / Chroma Cloud (paid).
- Or accept the reset for demo purposes and note it in the case study.
