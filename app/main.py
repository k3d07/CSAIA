import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.models import (
    ChatRequest, ChatResponse, Source,
    IngestRequest, IngestResponse,
    HealthResponse,
)
from app.agent import run_agent
from app.rag import ingest_text, ingest_directory, get_document_count

load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-key")


# ─────────────────────────────────────────────────────────────
# Startup: ingest knowledge base on first run
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup, ingest knowledge base if vector store is empty."""
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


# ─────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Customer Support AI Agent",
    description="LangChain agent with RAG over company knowledge base",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kedrichai.xyz",
        "https://www.kedrichai.xyz",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# ─────────────────────────────────────────────────────────────
# Auth dependency
# ─────────────────────────────────────────────────────────────

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    """Check API status and vector store document count."""
    return HealthResponse(
        status="ok",
        document_count=get_document_count(),
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _: str = Depends(verify_api_key),
):
    """
    Main endpoint. Send a customer support question, receive an answer
    with cited sources. Escalation happens automatically if needed.
    """
    try:
        result = await run_agent(
            message=request.message,
            conversation_history=[m.model_dump() for m in request.conversation_history],
        )

        sources = [Source(**s) for s in result["sources"]]

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            escalated=result["escalated"],
            session_id=request.session_id or str(uuid.uuid4()),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    request: IngestRequest,
    _: str = Depends(verify_api_key),
):
    """Add new content to the knowledge base without restarting."""
    try:
        chunks = ingest_text(
            content=request.content,
            document_name=request.document_name,
            metadata=request.metadata,
        )
        return IngestResponse(
            status="success",
            document_name=request.document_name,
            chunks_created=chunks,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("app/static/index.html")
