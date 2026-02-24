"""
RAG-Shared: Shared utilities and models for RAG-based Hindi QA system.

Ministry of Culture, Government of India.
"""

__version__ = "1.0.0"
__author__ = "RAG QA Team"

from rag_shared.models.language import Language
from rag_shared.models.health import HealthResponse, DependencyHealth
from rag_shared.models.errors import ErrorResponse, ErrorDetail

__all__ = [
    "Language",
    "HealthResponse",
    "DependencyHealth",
    "ErrorResponse",
    "ErrorDetail",
]
