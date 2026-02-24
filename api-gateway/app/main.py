"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from datetime import datetime
import logging
import structlog

from .config import get_settings
from .db.connection import Database
from .middleware.request_id import RequestIDMiddleware
from .middleware.audit_logger import AuditLoggerMiddleware
from .middleware.language_detector import LanguageDetectorMiddleware
from .middleware.rate_limiter import RateLimiterMiddleware
from .middleware.rbac import RBACMiddleware
from .routers import (
    health,
    chat,
    chat_stream,
    search,
    voice,
    translate,
    documents,
    feedback,
    ocr,
    analytics,
    admin,
)
from .utils.metrics import get_metrics
from . import __version__

# Setup logging
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

logger = logging.getLogger(__name__)

# Global state
db: Database = None
redis: Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global db, redis

    logger.info("Starting API Gateway")

    # Startup
    try:
        settings = get_settings()

        # Initialize database
        db = Database(settings.postgres_url)
        await db.initialize()
        logger.info("Database initialized")

        # Initialize Redis
        redis = await Redis.from_url(settings.redis_url, decode_responses=True)
        await redis.ping()
        logger.info("Redis connected")

        app.state.db = db
        app.state.redis = redis
        app.state.settings = settings

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down API Gateway")
    try:
        if db:
            await db.close()
        if redis:
            await redis.close()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title="Ministry of Culture RAG QA API",
    description="API Gateway for RAG-based Hindi QA system",
    version=__version__,
    lifespan=lifespan,
)

# Add middlewares (order matters - applied in reverse)
app.add_middleware(RBACMiddleware)
app.add_middleware(
    RateLimiterMiddleware,
    redis=None,  # Will be set at runtime
    rate_limits={
        "admin": get_settings().rate_limit_admin,
        "editor": get_settings().rate_limit_editor,
        "viewer": get_settings().rate_limit_viewer,
        "api_consumer": get_settings().rate_limit_api_consumer,
    },
)
app.add_middleware(AuditLoggerMiddleware)
app.add_middleware(LanguageDetectorMiddleware)
app.add_middleware(RequestIDMiddleware)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(chat_stream.router)
app.include_router(search.router)
app.include_router(voice.router)
app.include_router(translate.router)
app.include_router(documents.router)
app.include_router(feedback.router)
app.include_router(ocr.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Validation error: {exc}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(exc),
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled error: {exc}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": request_id,
            }
        },
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API documentation links."""
    return {
        "service": "api-gateway",
        "version": __version__,
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc",
        "health": "/api/v1/health",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
