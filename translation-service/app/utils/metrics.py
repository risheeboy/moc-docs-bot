"""Prometheus metrics for Translation Service"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from fastapi import FastAPI

# Global registry
_registry = CollectorRegistry()

# Metrics as per §11 Shared Contracts
# Standard HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
    registry=_registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=_registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request body size in bytes",
    labelnames=["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=_registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response body size in bytes",
    labelnames=["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=_registry,
)

# Translation service-specific metrics (from §11)
translation_duration_seconds = Histogram(
    "translation_duration_seconds",
    "Translation operation duration in seconds",
    labelnames=["source_language", "target_language"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=_registry,
)

translation_duration_histogram = Histogram(
    "translation_duration_seconds",
    "Translation operation duration in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=_registry,
)

translation_cache_hit_total = Counter(
    "translation_cache_hit_total",
    "Total translation cache hits",
    labelnames=["source_language", "target_language"],
    registry=_registry,
)

translation_cache_hit_counter = Counter(
    "translation_cache_hit_total",
    "Total translation cache hits",
    registry=_registry,
)

translation_cache_miss_total = Counter(
    "translation_cache_miss_total",
    "Total translation cache misses",
    labelnames=["source_language", "target_language"],
    registry=_registry,
)

# GPU model metrics
gpu_model_loaded = Gauge(
    "gpu_model_loaded",
    "Whether the translation model is loaded in GPU memory",
    labelnames=["model_name"],
    registry=_registry,
)

gpu_memory_usage_bytes = Gauge(
    "gpu_memory_usage_bytes",
    "GPU memory used by translation model in bytes",
    labelnames=["model_name"],
    registry=_registry,
)


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics endpoint for FastAPI app.

    Adds GET /metrics endpoint to the app.
    """

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            generate_latest(_registry),
            media_type="text/plain; charset=utf-8; version=0.0.4",
        )

    return app
