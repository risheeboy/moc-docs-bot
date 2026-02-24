import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    labelnames=["method", "endpoint"]
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size",
    labelnames=["method", "endpoint"]
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size",
    labelnames=["method", "endpoint"]
)

# RAG-specific metrics
rag_retrieval_duration_seconds = Histogram(
    "rag_retrieval_duration_seconds",
    "RAG retrieval latency",
    labelnames=["operation"]
)

rag_cache_hit_total = Counter(
    "rag_cache_hit_total",
    "Total cache hits"
)

rag_cache_miss_total = Counter(
    "rag_cache_miss_total",
    "Total cache misses"
)

rag_documents_ingested_total = Counter(
    "rag_documents_ingested_total",
    "Total documents ingested"
)

rag_chunks_created_total = Counter(
    "rag_chunks_created_total",
    "Total chunks created"
)

rag_retrieval_results = Histogram(
    "rag_retrieval_results",
    "Number of documents retrieved",
    labelnames=["operation"]
)
