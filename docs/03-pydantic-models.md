# 03 — Step 2: Pydantic Models

Source: lines 431–482 of source file. File: `app/models.py`.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_history: list[Message] = Field(default_factory=list)
    user_email: Optional[str] = None
    session_id: Optional[str] = None


class Source(BaseModel):
    document: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    escalated: bool = False
    session_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class IngestRequest(BaseModel):
    content: str = Field(..., min_length=10)
    document_name: str
    metadata: Optional[dict] = None


class IngestResponse(BaseModel):
    status: str
    document_name: str
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    document_count: int
    timestamp: str
```

## Notes
- `message` length: 1–5000 chars (validation at the boundary).
- `conversation_history` defaults to empty list (`default_factory=list` avoids the mutable-default trap).
- `timestamp` is generated server-side at response time via `default_factory=lambda: datetime.utcnow().isoformat()`.
- `metadata` on IngestRequest is `dict`-typed — used to tag arbitrary metadata (e.g. category, version) into Chroma.
