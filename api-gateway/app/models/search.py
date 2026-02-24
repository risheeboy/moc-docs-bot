"""Search request/response models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .common import Source, Multimedia, Event, Language


class SearchFilters(BaseModel):
    """Filters for search results."""
    source_sites: list[str] = Field(default_factory=list)
    content_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    language: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(default="en")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    filters: SearchFilters = Field(default_factory=SearchFilters)


class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    url: str
    snippet: str
    score: float = Field(ge=0.0, le=1.0)
    source_site: str
    language: str
    content_type: str
    thumbnail_url: Optional[str] = None
    published_date: Optional[str] = None
    ai_summary: Optional[str] = None


class SearchResponse(BaseModel):
    """Unified semantic search response."""
    results: list[SearchResult]
    multimedia: list[Multimedia] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    total_results: int
    page: int
    page_size: int
    cached: bool
    request_id: str
    timestamp: datetime


class SearchSuggestRequest(BaseModel):
    """Auto-complete suggestion request."""
    prefix: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en")
    limit: int = Field(default=10, ge=1, le=50)


class SearchSuggestResponse(BaseModel):
    """Auto-complete suggestions."""
    suggestions: list[str]
    request_id: str
