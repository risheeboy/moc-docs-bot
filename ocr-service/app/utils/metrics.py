"""Prometheus metrics for OCR Service."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import time

# Create a registry
_registry = CollectorRegistry()

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=_registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    registry=_registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request body size in bytes",
    ["method", "endpoint"],
    registry=_registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response body size in bytes",
    ["method", "endpoint"],
    registry=_registry,
)

# OCR-specific metrics
ocr_processing_duration_seconds = Histogram(
    "ocr_processing_duration_seconds",
    "OCR processing time in seconds",
    ["engine", "language"],
    registry=_registry,
)

ocr_files_processed_total = Counter(
    "ocr_files_processed_total",
    "Total files processed",
    ["engine", "status"],
    registry=_registry,
)

ocr_pages_processed_total = Counter(
    "ocr_pages_processed_total",
    "Total pages processed",
    ["engine"],
    registry=_registry,
)

ocr_confidence_histogram = Histogram(
    "ocr_confidence_score",
    "OCR confidence scores",
    ["engine", "language"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=_registry,
)

ocr_engine_errors_total = Counter(
    "ocr_engine_errors_total",
    "Total OCR engine errors",
    ["engine", "error_type"],
    registry=_registry,
)

pdf_pages_extracted_total = Counter(
    "pdf_pages_extracted_total",
    "Total PDF pages extracted",
    registry=_registry,
)

pdf_extraction_duration_seconds = Histogram(
    "pdf_extraction_duration_seconds",
    "PDF extraction time in seconds",
    registry=_registry,
)

# Service health metrics
service_startup_time = Gauge(
    "service_startup_time_seconds",
    "Service startup timestamp",
    registry=_registry,
)

service_uptime_seconds = Gauge(
    "service_uptime_seconds",
    "Service uptime in seconds",
    registry=_registry,
)


def setup_metrics():
    """Initialize metrics on service startup."""
    import time

    service_startup_time.set(time.time())


def get_metrics():
    """Get all metrics in Prometheus format."""
    return generate_latest(_registry).decode("utf-8")


def record_ocr_success(engine: str, language: str, duration_ms: float, confidence: float):
    """Record successful OCR processing."""
    ocr_processing_duration_seconds.labels(engine=engine, language=language).observe(
        duration_ms / 1000.0
    )
    ocr_files_processed_total.labels(engine=engine, status="success").inc()
    ocr_confidence_histogram.labels(engine=engine, language=language).observe(confidence)


def record_ocr_error(engine: str, error_type: str):
    """Record OCR error."""
    ocr_engine_errors_total.labels(engine=engine, error_type=error_type).inc()
    ocr_files_processed_total.labels(engine=engine, status="error").inc()


def record_pdf_extraction(num_pages: int, duration_ms: float):
    """Record PDF extraction."""
    pdf_pages_extracted_total.inc(num_pages)
    pdf_extraction_duration_seconds.observe(duration_ms / 1000.0)
