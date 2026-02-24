"""FastAPI application for Data Ingestion Engine."""

import logging
import structlog
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import jobs, targets, health
from app.utils.metrics import setup_prometheus_metrics


# Configure structured logging
def setup_logging():
    """Configure JSON structured logging with structlog."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
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

    # Set root logger level
    logging.basicConfig(
        level=getattr(logging, settings.app_log_level),
        format="%(message)s",
    )


setup_logging()
logger = structlog.get_logger()


# Lifespan handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info(
        "starting_service",
        service=settings.service_name,
        version=settings.service_version,
        port=settings.service_port,
    )

    # Setup Prometheus metrics
    setup_prometheus_metrics()

    yield

    # Shutdown
    logger.info(
        "shutting_down_service",
        service=settings.service_name,
    )


# Create FastAPI application
app = FastAPI(
    title="Data Ingestion Engine",
    description="Web scraping and content ingestion pipeline for Ministry of Culture RAG system",
    version=settings.service_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = request.headers.get("x-request-id", "")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(targets.router, prefix="/targets", tags=["targets"])


# Error handler for HTTP exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    import uuid

    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            }
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning service info."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
    }


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest

    return generate_latest()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=settings.app_debug,
        log_level=settings.app_log_level.lower(),
    )
