"""Main FastAPI application for Translation Service"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import translate, batch_translate, detect_language, health
from app.services.indictrans2_engine import indictrans2_engine
from app.utils.metrics import setup_metrics

# Configure structured logging
import structlog

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

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Translation service starting up", service="translation-service")
    try:
        await indictrans2_engine.initialize()
        logger.info(
            "IndicTrans2 model loaded successfully",
            model=settings.translation_model,
        )
    except Exception as e:
        logger.error("Failed to load IndicTrans2 model", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Translation service shutting down")
    await indictrans2_engine.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Translation Service",
    description="IndicTrans2-based translation microservice for Indian languages",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup Prometheus metrics
setup_metrics(app)

# Include routers
app.include_router(translate.router)
app.include_router(batch_translate.router)
app.include_router(detect_language.router)
app.include_router(health.router)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add X-Request-ID to all responses"""
    request_id = request.headers.get("X-Request-ID", "")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "translation-service",
        "version": "1.0.0",
        "status": "running",
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(
        "Unhandled exception",
        error=str(exc),
        request_id=request_id,
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
        port=8004,
        log_level=settings.app_log_level.lower(),
    )
