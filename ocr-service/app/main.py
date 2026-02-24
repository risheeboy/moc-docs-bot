"""FastAPI application for OCR Service."""

import time
import logging
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import ocr, batch, health
from app.utils.metrics import setup_metrics

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    format="%(message)s",
    stream=None,
    level=getattr(logging, settings.log_level),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("ocr_service_starting", service=settings.service_name, version=settings.version)
    setup_metrics()
    yield
    # Shutdown
    logger.info("ocr_service_stopping", service=settings.service_name)


# Create FastAPI application
app = FastAPI(
    title="OCR Service",
    description="Document digitization for Hindi and English content",
    version=settings.version,
    lifespan=lifespan,
)

# Add middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for gzip compression
app.add_middleware(GZIPMiddleware, minimum_size=1000)


# Request ID and logging middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()

    # Store request ID in scope for use in routes
    request.state.request_id = request_id

    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    # Log request
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )

    return response


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
app.include_router(batch.router, prefix="/ocr/batch", tags=["batch"])


@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint."""
    from app.utils.metrics import get_metrics

    metrics_text = get_metrics()
    return Response(content=metrics_text, media_type="text/plain")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
                "request_id": request_id,
            }
        },
    )


@app.get("/")
async def root(request: Request):
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.version,
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_config=None,  # Use our structlog config
    )
