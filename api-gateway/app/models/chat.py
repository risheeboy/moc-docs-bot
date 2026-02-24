"""Chat request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from .common import Source, Language


class ChatMessage(BaseModel):
    """Message in chat history."""
    role: Literal["user", "assistant"]
    content: str


class ChatFilters(BaseModel):
    """Filters for RAG retrieval."""
    source_sites: list[str] = Field(default_factory=list)
    content_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat query request."""
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")
    session_id: Optional[str] = None
    chat_history: list[ChatMessage] = Field(default_factory=list)
    top_k: int = Field(default=10, ge=1, le=50)
    filters: ChatFilters = Field(default_factory=ChatFilters)


class ChatResponse(BaseModel):
    """Chat query response."""
    response: str
    sources: list[Source]
    confidence: float = Field(ge=0.0, le=1.0)
    session_id: str
    language: str
    model_used: str
    cached: bool
    request_id: str
    timestamp: datetime


class ChatStreamResponse(BaseModel):
    """Streamed chunk of chat response."""
    content: str
    delta: str
    sources: list[Source] = Field(default_factory=list)
    confidence: Optional[float] = None
    session_id: str
    model_used: str
    request_id: str
