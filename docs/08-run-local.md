# 08 — Step 7: Run Locally

Source: lines 1367–1381 of source file.

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs — FastAPI auto-docs.

## First Startup Log (expected)
```
Vector store is empty. Ingesting knowledge base...
Ingested 47 chunks from knowledge base.
```

## Troubleshooting
- **No log line at all** → app didn't start. Check uvicorn output for tracebacks.
- **"OpenAI authentication failed"** → `.env` not loaded, or key invalid. `python-dotenv` is loaded in every module that needs env vars; double-check via `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY')[:8])"`.
- **"FileNotFoundError: knowledge_base"** → run uvicorn from the repo root, not from `app/`.
- **Chunk count == 0** → docs may all be empty or wrong extension.
