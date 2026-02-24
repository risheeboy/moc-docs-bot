"""Prometheus metrics exposition."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from typing import Optional
import time

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size",
    ["method", "endpoint"],
)

# Service-specific metrics
llm_tokens_generated_total = Counter(
    "llm_tokens_generated_total",
    "Total LLM tokens generated",
    ["model"],
)

llm_inference_duration_seconds = Histogram(
    "llm_inference_duration_seconds",
    "LLM inference latency",
    ["model"],
)

llm_model_loaded = Gauge(
    "llm_model_loaded",
    "Whether LLM model is loaded",
    ["model"],
)

rag_retrieval_duration_seconds = Histogram(
    "rag_retrieval_duration_seconds",
    "RAG retrieval latency",
)

rag_cache_hit_total = Counter(
    "rag_cache_hit_total",
    "Cache hit count",
)

rag_cache_miss_total = Counter(
    "rag_cache_miss_total",
    "Cache miss count",
)


def record_http_request(method: str, endpoint: str, status_code: int, duration_seconds: float):
    """Record HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration_seconds
    )


def record_llm_call(model: str, tokens: int, duration_seconds: float):
    """Record LLM call metrics."""
    llm_tokens_generated_total.labels(model=model).inc(tokens)
    llm_inference_duration_seconds.labels(model=model).observe(duration_seconds)


def record_rag_retrieval(duration_seconds: float):
    """Record RAG retrieval metrics."""
    rag_retrieval_duration_seconds.observe(duration_seconds)


def record_cache_hit():
    """Record cache hit."""
    rag_cache_hit_total.inc()


def record_cache_miss():
    """Record cache miss."""
    rag_cache_miss_total.inc()


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    return generate_latest(REGISTRY)
