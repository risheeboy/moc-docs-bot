"""Pydantic models for API requests and responses."""

from .common import (
    Language,
    ErrorDetail,
    ErrorResponse,
    DependencyHealth,
    HealthResponse,
    Pagination,
    PaginatedResponse,
    Source,
    Multimedia,
    Event,
)
from .chat import ChatRequest, ChatResponse, ChatStreamResponse
from .search import SearchRequest, SearchResponse, SearchResult
from .voice import STTRequest, STTResponse, TTSRequest, TTSResponse
from .translate import TranslateRequest, TranslateResponse, TranslateBatchRequest, TranslateBatchResponse
from .document import DocumentUpload, DocumentResponse, DocumentListResponse
from .feedback import FeedbackCreate, FeedbackResponse
from .analytics import AnalyticsSummary, QueryStats

__all__ = [
    "Language",
    "ErrorDetail",
    "ErrorResponse",
    "DependencyHealth",
    "HealthResponse",
    "Pagination",
    "PaginatedResponse",
    "Source",
    "Multimedia",
    "Event",
    "ChatRequest",
    "ChatResponse",
    "ChatStreamResponse",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "STTRequest",
    "STTResponse",
    "TTSRequest",
    "TTSResponse",
    "TranslateRequest",
    "TranslateResponse",
    "TranslateBatchRequest",
    "TranslateBatchResponse",
    "DocumentUpload",
    "DocumentResponse",
    "DocumentListResponse",
    "FeedbackCreate",
    "FeedbackResponse",
    "AnalyticsSummary",
    "QueryStats",
]
