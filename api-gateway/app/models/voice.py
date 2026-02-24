"""Voice (STT/TTS) request/response models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class STTRequest(BaseModel):
    """Speech-to-text request (sent as multipart/form-data in actual API)."""
    language: Optional[str] = Field(default="auto", description="Language code or 'auto'")


class STTResponse(BaseModel):
    """Speech-to-text response."""
    text: str
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    duration_seconds: float
    request_id: str
    timestamp: datetime


class TTSRequest(BaseModel):
    """Text-to-speech request."""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en")
    format: Literal["mp3", "wav", "ogg"] = Field(default="mp3")
    voice: str = Field(default="default")


class TTSResponse(BaseModel):
    """Text-to-speech response metadata."""
    duration_seconds: float
    language: str
    format: str
    request_id: str
    timestamp: datetime
