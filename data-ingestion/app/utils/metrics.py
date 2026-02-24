"""Prometheus metrics for Data Ingestion Service."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# Ingestion metrics (per §11)
ingestion_pages_crawled_total = Counter(
    "ingestion_pages_crawled_total",
    "Total pages crawled by ingestion service",
    ["spider_type"],
)

ingestion_documents_ingested_total = Counter(
    "ingestion_documents_ingested_total",
    "Total documents ingested into RAG",
    ["content_type", "language"],
)

ingestion_errors_total = Counter(
    "ingestion_errors_total",
    "Total ingestion errors",
    ["error_type"],
)

# Job metrics
job_counter = Counter(
    "ingestion_jobs_total",
    "Total scraping jobs triggered",
    ["status"],
)

job_duration_seconds = Histogram(
    "ingestion_job_duration_seconds",
    "Job execution duration in seconds",
    ["spider_type"],
)

active_jobs_gauge = Gauge(
    "ingestion_active_jobs",
    "Number of currently active scraping jobs",
)

# Scraper metrics
scrape_pages_total = Counter(
    "ingestion_scrape_pages_total",
    "Total pages scraped",
)

scrape_duration_seconds = Histogram(
    "ingestion_scrape_duration_seconds",
    "Time to scrape a single page",
    ["spider_type"],
)

# Parser metrics
parsing_errors_total = Counter(
    "ingestion_parsing_errors_total",
    "Total parsing errors",
    ["parser_type"],
)

chunking_errors_total = Counter(
    "ingestion_chunking_errors_total",
    "Total chunking errors",
)

# Deduplication metrics
dedup_duplicates_detected = Counter(
    "ingestion_dedup_duplicates_total",
    "Total duplicate documents detected",
)

# Storage metrics
s3_upload_errors_total = Counter(
    "ingestion_s3_upload_errors_total",
    "Total S3 upload errors",
)

documents_stored_bytes = Histogram(
    "ingestion_documents_stored_bytes",
    "Size of documents stored in S3",
    ["document_type"],
)

# Language detection metrics
language_detection_duration_seconds = Histogram(
    "ingestion_language_detection_seconds",
    "Time to detect document language",
)

# RAG service integration metrics
rag_ingest_requests_total = Counter(
    "ingestion_rag_ingest_requests_total",
    "Total requests to RAG service /ingest endpoint",
    ["status"],
)

rag_ingest_duration_seconds = Histogram(
    "ingestion_rag_ingest_duration_seconds",
    "Time to ingest document in RAG service",
)


def setup_prometheus_metrics():
    """Setup Prometheus metrics for this service.

    This is called during application startup.
    """
    # All metrics are registered automatically when created
    pass


def record_http_request(method: str, endpoint: str, status_code: int, duration: float, request_size: int, response_size: int):
    """Record HTTP request metrics.

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: Response status code
        duration: Request duration in seconds
        request_size: Request size in bytes
        response_size: Response size in bytes
    """
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)

    http_request_size_bytes.labels(
        method=method,
        endpoint=endpoint,
    ).observe(request_size)

    http_response_size_bytes.labels(
        method=method,
        endpoint=endpoint,
    ).observe(response_size)


def record_ingestion_success(content_type: str, language: str):
    """Record successful document ingestion.

    Args:
        content_type: Type of content (webpage, pdf, etc)
        language: Document language code
    """
    ingestion_documents_ingested_total.labels(
        content_type=content_type,
        language=language,
    ).inc()


def record_ingestion_error(error_type: str):
    """Record ingestion error.

    Args:
        error_type: Type of error
    """
    ingestion_errors_total.labels(error_type=error_type).inc()


def record_job_completion(spider_type: str, duration: float):
    """Record completed job.

    Args:
        spider_type: Type of spider
        duration: Job duration in seconds
    """
    job_duration_seconds.labels(spider_type=spider_type).observe(duration)
