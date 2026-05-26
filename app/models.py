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
