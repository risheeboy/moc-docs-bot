"""Translation request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TranslateRequest(BaseModel):
    """Single text translation request."""
    text: str = Field(..., min_length=1, max_length=10000)
    source_language: str = Field(default="en")
    target_language: str = Field(default="hi")


class TranslateResponse(BaseModel):
    """Single text translation response."""
    translated_text: str
    source_language: str
    target_language: str
    cached: bool
    request_id: str
    timestamp: datetime


class TranslateBatchRequest(BaseModel):
    """Batch translation request."""
    texts: list[str] = Field(..., min_items=1, max_items=100)
    source_language: str = Field(default="en")
    target_language: str = Field(default="hi")


class TranslationItem(BaseModel):
    """Individual translation in batch response."""
    text: str
    cached: bool


class TranslateBatchResponse(BaseModel):
    """Batch translation response."""
    translations: list[TranslationItem]
    source_language: str
    target_language: str
    request_id: str
    timestamp: datetime


class DetectRequest(BaseModel):
    """Language detection request."""
    text: str = Field(..., min_length=1, max_length=5000)


class DetectResponse(BaseModel):
    """Language detection response."""
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    script: Optional[str] = None
    request_id: str
    timestamp: datetime
