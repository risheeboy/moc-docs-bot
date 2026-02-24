"""Common Pydantic models used across the API."""

from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime
from enum import Enum
from uuid import UUID


class Language(str, Enum):
    """Supported language codes (ISO 639-1)."""
    HI = "hi"
    EN = "en"
    BN = "bn"
    TE = "te"
    MR = "mr"
    TA = "ta"
    UR = "ur"
    GU = "gu"
    KN = "kn"
    ML = "ml"
    OR = "or"
    PA = "pa"
    AS_ = "as"
    MAI = "mai"
    SA = "sa"
    NE = "ne"
    SD = "sd"
    KOK = "kok"
    DOI = "doi"
    MNI = "mni"
    SAT = "sat"
    BO = "bo"
    KS = "ks"


class ErrorDetail(BaseModel):
    """Error response detail."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description")
    details: Optional[dict[str, Any]] = Field(default=None)
    request_id: Optional[str] = Field(default=None)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail


class DependencyHealth(BaseModel):
    """Health status of a service dependency."""
    status: Literal["healthy", "degraded", "unhealthy"]
    latency_ms: float


class HealthResponse(BaseModel):
    """Standard health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    version: str
    uptime_seconds: float
    timestamp: datetime
    dependencies: dict[str, DependencyHealth]


class Pagination(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[Any]


class Source(BaseModel):
    """Citation source for retrieved context."""
    title: str
    url: str
    snippet: str
    score: float = Field(ge=0.0, le=1.0)
    source_site: str
    language: str
    content_type: str
    chunk_id: str


class Multimedia(BaseModel):
    """Multimedia result (image/video)."""
    type: Literal["image", "video"]
    url: str
    alt_text: Optional[str] = None
    source_site: str
    thumbnail_url: Optional[str] = None


class Event(BaseModel):
    """Event result."""
    title: str
    date: str  # ISO format date
    venue: str
    description: str
    source_url: str
    language: str
