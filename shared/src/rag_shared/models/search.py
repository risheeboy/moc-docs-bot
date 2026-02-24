"""Search result models for semantic search interface."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SearchResult(BaseModel):
    """Single search result from RAG retrieval."""

    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    snippet: str = Field(..., description="AI-generated summary snippet")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score",
    )
    source_site: str = Field(..., description="Source domain (e.g., asi.nic.in)")
    language: str = Field(
        default="en",
        description="Language code",
    )
    content_type: str = Field(
        default="webpage",
        description="webpage | pdf | document | etc",
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="MinIO thumbnail URL if available",
    )
    published_date: Optional[str] = Field(
        default=None,
        description="Publication date in ISO 8601",
    )

    model_config = ConfigDict(from_attributes=True)


class MultimediaResult(BaseModel):
    """Image or video result from search."""

    type: str = Field(
        ...,
        description="image | video | audio",
    )
    url: str = Field(..., description="Direct URL to multimedia")
    alt_text: str = Field(..., description="Accessibility alt text")
    source_site: str = Field(..., description="Source domain")
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="MinIO thumbnail URL",
    )

    model_config = ConfigDict(from_attributes=True)


class EventResult(BaseModel):
    """Cultural event result."""

    title: str = Field(..., description="Event title")
    date: str = Field(..., description="Event date in ISO 8601")
    venue: str = Field(..., description="Event venue/location")
    description: str = Field(..., description="Event description")
    source_url: str = Field(..., description="Source URL")
    language: str = Field(
        default="en",
        description="Event information language",
    )

    model_config = ConfigDict(from_attributes=True)
