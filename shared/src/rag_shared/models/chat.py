"""Chat-related models for conversation data."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ChatMessage(BaseModel):
    """Single message in a conversation."""

    role: str = Field(
        ...,
        description="Message role: user | assistant | system",
    )
    content: str = Field(..., description="Message text")
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 UTC timestamp",
    )

    model_config = ConfigDict(from_attributes=True)


class Source(BaseModel):
    """Source document reference for RAG retrieval."""

    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Source URL")
    snippet: str = Field(..., description="Relevant text snippet")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score from retrieval",
    )
    source_site: str = Field(..., description="Domain name (e.g., culture.gov.in)")
    language: str = Field(
        default="en",
        description="Language code (ISO 639-1)",
    )
    content_type: str = Field(
        default="webpage",
        description="Content type: webpage | pdf | document | etc",
    )
    chunk_id: Optional[str] = Field(
        default=None,
        description="Milvus vector ID for this chunk",
    )

    model_config = ConfigDict(from_attributes=True)
