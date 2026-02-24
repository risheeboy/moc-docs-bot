"""Feedback request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class FeedbackCreate(BaseModel):
    """Feedback submission."""
    session_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    response: str = Field(..., min_length=1, max_length=5000)
    rating: int = Field(ge=1, le=5, description="1=poor, 5=excellent")
    feedback_text: Optional[str] = Field(None, max_length=2000)
    feedback_type: Literal["chat", "search"]
    language: str = Field(default="en")


class FeedbackResponse(BaseModel):
    """Feedback response."""
    feedback_id: str
    session_id: str
    rating: int
    feedback_type: str
    sentiment_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sentiment_label: Optional[Literal["positive", "neutral", "negative"]] = None
    created_at: datetime
    request_id: str
