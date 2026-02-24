"""Main FastAPI application for Speech Service"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import REGISTRY, generate_latest

from app import __version__
from app.config import config
from app.routers import health, stt, tts
from app.utils.metrics import set_gpu_available, set_models_loaded
from app.services.indic_conformer_stt import get_stt_model
from app.services.indic_tts import get_hindi_tts_model
from app.services.coqui_tts import get_english_tts_model

# Configure structured logging
def setup_logging():
    """Configure structured JSON logging with structlog"""
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

    # Setup root logger
    logging.basicConfig(
        format="%(message)s",
        level=config.log_level,
    )


# Setup logging on import
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(
        "speech_service_startup",
        event="startup",
        version=__version__,
        environment=config.app_env,
    )

    try:
        # Load models on startup
        logger.info("Loading AI models on startup...")
        stt_model = get_stt_model()
        hindi_tts = get_hindi_tts_model()
        english_tts = get_english_tts_model()

        models_loaded = sum(
            [
                stt_model.check_model_loaded(),
                hindi_tts.check_model_loaded(),
                english_tts.check_model_loaded(),
            ]
        )
        set_models_loaded(models_loaded)

        logger.info(
            "models_loaded",
            event="models_loaded",
            stt_loaded=stt_model.check_model_loaded(),
            hindi_tts_loaded=hindi_tts.check_model_loaded(),
            english_tts_loaded=english_tts.check_model_loaded(),
        )

        # Check GPU availability
        import torch
        gpu_available = torch.cuda.is_available()
        set_gpu_available(gpu_available)
        logger.info(
            "gpu_status",
            event="gpu_check",
            gpu_available=gpu_available,
            cuda_version=torch.version.cuda if gpu_available else None,
        )

    except Exception as e:
        logger.error(
            "startup_error",
            event="startup_error",
            error=str(e),
            exc_info=True,
        )

    yield

    # Shutdown
    logger.info(
        "speech_service_shutdown",
        event="shutdown",
    )


# Create FastAPI app
app = FastAPI(
    title="Speech Service",
    description="AI4Bharat IndicConformer STT + IndicTTS/Coqui TTS",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for tracing"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())

    # Add to request state
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# Request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all HTTP requests"""
    import time

    start_time = time.time()
    path = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "http_request",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=process_time * 1000,
            request_id=getattr(request.state, "request_id", None),
        )

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "http_error",
            method=method,
            path=path,
            duration_ms=process_time * 1000,
            error=str(e),
            request_id=getattr(request.state, "request_id", None),
        )
        raise


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(stt.router, tags=["speech-to-text"])
app.include_router(tts.router, tags=["text-to-speech"])


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (from shared contracts §11)"""
    return generate_latest(REGISTRY)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - service info"""
    return {
        "service": "speech-service",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "stt": "/stt",
            "tts": "/tts",
            "metrics": "/metrics",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "unhandled_exception",
        error=str(exc),
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_config=None,  # Use our structlog setup
    )
