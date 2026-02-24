"""Models package for RAG-shared."""

from rag_shared.models.language import Language
from rag_shared.models.errors import ErrorDetail, ErrorResponse
from rag_shared.models.health import DependencyHealth, HealthResponse
from rag_shared.models.chat import ChatMessage, Source
from rag_shared.models.search import SearchResult, MultimediaResult, EventResult
from rag_shared.models.document import Document
from rag_shared.models.pagination import PaginatedRequest, PaginatedResponse

__all__ = [
    "Language",
    "ErrorDetail",
    "ErrorResponse",
    "DependencyHealth",
    "HealthResponse",
    "ChatMessage",
    "Source",
    "SearchResult",
    "MultimediaResult",
    "EventResult",
    "Document",
    "PaginatedRequest",
    "PaginatedResponse",
]
