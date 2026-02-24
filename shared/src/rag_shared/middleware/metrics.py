"""Prometheus metrics middleware (§11 of Shared Contracts)."""

from typing import Optional, Callable, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
import logging

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """Prometheus metrics for HTTP requests.

    Provides automatic instrumentation for:
    - http_requests_total: Counter with method, endpoint, status_code labels
    - http_request_duration_seconds: Histogram with method, endpoint labels
    - http_request_size_bytes: Histogram with method, endpoint labels
    - http_response_size_bytes: Histogram with method, endpoint labels
    """

    def __init__(self, app: Any, service_name: str, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics middleware.

        Args:
            app: FastAPI application
            service_name: Service name for metrics labels
            registry: Optional Prometheus registry (default: default registry)
        """
        self.app = app
        self.service_name = service_name
        self.registry = registry

        # Initialize metrics
        self.requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            registry=registry,
        )

        self.request_size_bytes = Histogram(
            "http_request_size_bytes",
            "HTTP request size in bytes",
            ["method", "endpoint"],
            registry=registry,
        )

        self.response_size_bytes = Histogram(
            "http_response_size_bytes",
            "HTTP response size in bytes",
            ["method", "endpoint"],
            registry=registry,
        )

    async def __call__(self, scope: Any, receive: Callable, send: Callable) -> None:
        """ASGI middleware handler."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Track request size
        request_size = 0

        # Wrap receive to track request size
        async def receive_with_size() -> dict:
            nonlocal request_size
            message = await receive()
            if message["type"] == "http.request":
                request_size += len(message.get("body", b""))
            return message

        # Track response
        response_size = 0
        status_code = 500
        start_time = time.time()

        async def send_with_metrics(message: dict) -> None:
            nonlocal response_size, status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))

            await send(message)

        try:
            await self.app(scope, receive_with_size, send_with_metrics)
        finally:
            # Record metrics
            duration = time.time() - start_time

            # Normalize endpoint path (remove IDs to reduce cardinality)
            endpoint = self._normalize_path(path)

            self.requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            self.request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            if request_size > 0:
                self.request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(request_size)

            if response_size > 0:
                self.response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(response_size)

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path to reduce metric cardinality.

        Replaces numeric IDs and UUIDs with placeholders.

        Args:
            path: Request path

        Returns:
            Normalized path
        """
        import re

        # Replace UUIDs with {id}
        path = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{id}", path)

        # Replace numeric IDs with {id}
        path = re.sub(r"/\d+", "/{id}", path)

        return path


def get_metrics_middleware(app: Any, service_name: str) -> MetricsMiddleware:
    """Create and return metrics middleware for FastAPI app.

    Args:
        app: FastAPI application
        service_name: Service name for labels

    Returns:
        Configured MetricsMiddleware instance
    """
    return MetricsMiddleware(app, service_name)


# Service-specific metric helpers
class RAGMetrics:
    """RAG service specific metrics."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize RAG metrics."""
        self.retrieval_duration = Histogram(
            "rag_retrieval_duration_seconds",
            "RAG document retrieval latency",
            ["operation"],
            registry=registry,
        )

        self.cache_hits = Counter(
            "rag_cache_hit_total",
            "RAG cache hits",
            ["collection"],
            registry=registry,
        )

        self.cache_misses = Counter(
            "rag_cache_miss_total",
            "RAG cache misses",
            ["collection"],
            registry=registry,
        )


class LLMMetrics:
    """LLM service specific metrics."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize LLM metrics."""
        self.tokens_generated = Counter(
            "llm_tokens_generated_total",
            "LLM tokens generated",
            ["model"],
            registry=registry,
        )

        self.inference_duration = Histogram(
            "llm_inference_duration_seconds",
            "LLM inference latency",
            ["model"],
            registry=registry,
        )

        self.model_loaded = Gauge(
            "llm_model_loaded",
            "LLM model loaded status (1=loaded, 0=unloaded)",
            ["model"],
            registry=registry,
        )


class SpeechMetrics:
    """Speech service specific metrics."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize speech metrics."""
        self.stt_duration = Histogram(
            "speech_stt_duration_seconds",
            "Speech-to-text latency",
            registry=registry,
        )

        self.tts_duration = Histogram(
            "speech_tts_duration_seconds",
            "Text-to-speech latency",
            registry=registry,
        )


class TranslationMetrics:
    """Translation service specific metrics."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize translation metrics."""
        self.translation_duration = Histogram(
            "translation_duration_seconds",
            "Translation latency",
            ["source_lang", "target_lang"],
            registry=registry,
        )

        self.cache_hits = Counter(
            "translation_cache_hit_total",
            "Translation cache hits",
            registry=registry,
        )


class IngestionMetrics:
    """Data ingestion service specific metrics."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize ingestion metrics."""
        self.pages_crawled = Counter(
            "ingestion_pages_crawled_total",
            "Total pages crawled",
            ["spider"],
            registry=registry,
        )

        self.documents_ingested = Counter(
            "ingestion_documents_ingested_total",
            "Total documents ingested",
            ["content_type"],
            registry=registry,
        )

        self.errors_total = Counter(
            "ingestion_errors_total",
            "Total ingestion errors",
            ["error_type"],
            registry=registry,
        )
