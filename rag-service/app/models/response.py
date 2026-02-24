from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


class Source(BaseModel):
    """Source document for a retrieved chunk."""
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    snippet: str = Field(..., description="Relevant text snippet")
    score: float = Field(..., description="Retrieval score")
    source_site: str = Field(..., description="Source site domain")
    language: str = Field(..., description="Content language")
    content_type: str = Field(..., description="Content type")
    chunk_id: str = Field(..., description="Milvus chunk ID")


class QueryResponse(BaseModel):
    """Response for chatbot query."""
    context: str = Field(..., description="Assembled context for LLM generation")
    sources: List[Source] = Field(..., description="Retrieved sources")
    confidence: float = Field(..., description="Overall confidence score")
    cached: bool = Field(default=False, description="Whether result was from cache")


class SearchResult(BaseModel):
    """Single search result."""
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    snippet: str = Field(..., description="AI-generated snippet")
    score: float = Field(..., description="Relevance score")
    source_site: str = Field(..., description="Source site domain")
    language: str = Field(..., description="Content language")
    content_type: str = Field(..., description="Content type")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL from MinIO")
    published_date: Optional[str] = Field(default=None, description="Publication date (ISO 8601)")


class MultimediaResult(BaseModel):
    """Multimedia result (image/video)."""
    type: str = Field(..., description="Media type: 'image' or 'video'")
    url: str = Field(..., description="Media URL")
    alt_text: Optional[str] = Field(default=None, description="Alternative text")
    source_site: str = Field(..., description="Source site domain")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")


class EventResult(BaseModel):
    """Event listing."""
    title: str = Field(..., description="Event title")
    date: str = Field(..., description="Event date (ISO 8601)")
    venue: str = Field(..., description="Event venue")
    description: str = Field(..., description="Event description")
    source_url: str = Field(..., description="Source URL")
    language: str = Field(..., description="Event language")


class SearchResponse(BaseModel):
    """Response for semantic search."""
    results: List[SearchResult] = Field(..., description="Search results")
    multimedia: Optional[List[MultimediaResult]] = Field(default=[], description="Multimedia results")
    events: Optional[List[EventResult]] = Field(default=[], description="Event listings")
    total_results: int = Field(..., description="Total result count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Results per page")
    cached: bool = Field(default=False, description="Whether result was from cache")


class IngestResponse(BaseModel):
    """Response for document ingestion."""
    document_id: str = Field(..., description="Document ID")
    chunk_count: int = Field(..., description="Number of chunks created")
    embedding_status: str = Field(..., description="Status of embedding (e.g., 'completed')")
    milvus_ids: List[str] = Field(..., description="Milvus chunk IDs")


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    status: str = Field(..., description="Health status: 'healthy', 'degraded', or 'unhealthy'")
    latency_ms: float = Field(..., description="Latency in milliseconds")


class HealthResponse(BaseModel):
    """Service health check response."""
    status: str = Field(..., description="Overall status: 'healthy', 'degraded', or 'unhealthy'")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    timestamp: datetime = Field(..., description="Current timestamp")
    dependencies: Dict[str, DependencyHealth] = Field(..., description="Dependency status map")


class ErrorDetail(BaseModel):
    """Error response detail."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail
