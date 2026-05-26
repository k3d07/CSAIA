# 07 — Step 6: FastAPI Application

Source: lines 1213–1363 of source file. File: `app/main.py`.

## App Setup
```python
app = FastAPI(
    title="Customer Support AI Agent",
    description="LangChain agent with RAG over company knowledge base",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```

## Lifespan — Auto-Ingest on Empty
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        count = get_document_count()
        if count == 0:
            print("Vector store is empty. Ingesting knowledge base...")
            chunks = ingest_directory("./knowledge_base")
            print(f"Ingested {chunks} chunks from knowledge base.")
        else:
            print(f"Vector store ready. {count} chunks loaded.")
    except Exception as e:
        print(f"Startup ingestion warning: {e}")
    yield
```

## Auth Dependency
```python
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```
`API_KEY = os.getenv("API_KEY", "dev-key")` — fallback `"dev-key"` is dev-only, override in `.env`.

## Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | none | banner JSON |
| GET | `/health` | none | status + doc count |
| POST | `/chat` | x-api-key | main entrypoint |
| POST | `/ingest` | x-api-key | add doc to vector store |

`/chat` body → calls `run_agent`, maps result["sources"] to `Source` Pydantic models, returns `ChatResponse` with `session_id` (existing or new UUID4).

`/ingest` body → calls `ingest_text`, returns chunk count.

Both wrap `run_agent` / `ingest_text` in try/except → 500 with error string.

## Note on `/escalate`
The overview mentions a `POST /escalate` endpoint, but the implementation in the source file does NOT expose it as a separate route. Escalation happens implicitly via the `escalate_to_human` tool inside `/chat`. **Decision point:** confirm whether to add a direct `/escalate` endpoint, or trust the in-band escalation pattern. We'll discuss when we reach this section.
