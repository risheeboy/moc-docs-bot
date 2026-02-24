"""FastAPI application for model training service."""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from app.config import get_config
from app.routers import evaluate, finetune, health
from app.utils.logging_config import setup_json_logging

# Setup logging
logger = setup_json_logging("model-training")
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Model training service starting", extra={"version": config.SERVICE_VERSION})
    yield
    # Shutdown
    logger.info("Model training service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Model Training Service",
    description="QLoRA fine-tuning and evaluation pipeline for Ministry of Culture domain-adapted LLMs",
    version=config.SERVICE_VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    """Add request ID tracking."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(finetune.router, prefix="/finetune", tags=["Fine-tuning"])
app.include_router(evaluate.router, prefix="/evaluate", tags=["Evaluation"])


@app.get("/", tags=["Root"])
async def root(x_request_id: Optional[str] = Header(None)):
    """Root endpoint."""
    return {
        "service": "model-training",
        "version": config.SERVICE_VERSION,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
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
        port=8007,
        log_config=None,  # Use structured logging
    )
