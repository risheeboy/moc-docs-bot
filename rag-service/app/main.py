import logging
import sys
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.config import settings
from app.routers import health, query, search, ingest
from app.utils.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes
)
import time
import uuid

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, settings.app_log_level),
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG Service",
    description="Retrieval-Augmented Generation pipeline for Ministry of Culture QA",
    version="1.0.0"
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(query.router, tags=["retrieval"])
app.include_router(search.router, tags=["search"])
app.include_router(ingest.router, tags=["ingestion"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Middleware to record HTTP metrics.

    Measures request latency, sizes, and status codes.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Extract endpoint name
    endpoint = request.url.path
    method = request.method

    # Record metrics
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(process_time)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "rag-service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": request_id
            }
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting RAG Service")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug: {settings.app_debug}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level=settings.app_log_level.lower()
    )
