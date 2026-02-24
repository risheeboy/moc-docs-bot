"""Middleware package for logging and metrics."""

from rag_shared.middleware.logging import setup_json_logging, get_logger
from rag_shared.middleware.metrics import MetricsMiddleware, get_metrics_middleware

__all__ = [
    "setup_json_logging",
    "get_logger",
    "MetricsMiddleware",
    "get_metrics_middleware",
]
