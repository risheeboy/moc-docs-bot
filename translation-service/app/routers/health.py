"""Health check endpoint"""

import time
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.cache import translation_cache
from app.services.indictrans2_engine import indictrans2_engine

logger = structlog.get_logger()

router = APIRouter(tags=["health"])

# Track startup time
_startup_time = time.time()


class DependencyHealth(BaseModel):
    """Health status of a dependency"""

    status: str = Field(..., description="healthy | degraded | unhealthy")
    latency_ms: float = Field(..., description="Response time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response (from §5 Shared Contracts)"""

    status: str = Field(
        ..., description="healthy | degraded | unhealthy"
    )
    service: str = Field(..., description="Service name (translation-service)")
    version: str = Field(..., description="Semantic version")
    uptime_seconds: float = Field(..., description="Seconds since startup")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    dependencies: dict[str, DependencyHealth] = Field(
        ..., description="Map of dependency health status"
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and dependency health.
    From §5 Shared Contracts.
    """
    dependencies: dict[str, DependencyHealth] = {}
    overall_status = "healthy"

    # Check Redis connectivity
    try:
        start = time.time()
        redis_healthy = await translation_cache.health_check()
        latency_ms = (time.time() - start) * 1000

        if redis_healthy:
            dependencies["redis"] = DependencyHealth(
                status="healthy", latency_ms=latency_ms
            )
        else:
            dependencies["redis"] = DependencyHealth(
                status="unhealthy", latency_ms=latency_ms
            )
            overall_status = "degraded"
    except Exception as e:
        logger.warning("Redis health check failed", error=str(e))
        dependencies["redis"] = DependencyHealth(
            status="unhealthy", latency_ms=0.0
        )
        overall_status = "degraded"

    # Check GPU and model loading
    try:
        start = time.time()
        model_healthy = await indictrans2_engine.health_check()
        latency_ms = (time.time() - start) * 1000

        if model_healthy:
            dependencies["gpu_model"] = DependencyHealth(
                status="healthy", latency_ms=latency_ms
            )
        else:
            dependencies["gpu_model"] = DependencyHealth(
                status="unhealthy", latency_ms=latency_ms
            )
            overall_status = "unhealthy"
    except Exception as e:
        logger.warning("GPU/Model health check failed", error=str(e))
        dependencies["gpu_model"] = DependencyHealth(
            status="unhealthy", latency_ms=0.0
        )
        overall_status = "unhealthy"

    # Calculate uptime
    uptime_seconds = time.time() - _startup_time

    # If model is unhealthy, return 503
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service is unhealthy")

    return HealthResponse(
        status=overall_status,
        service="translation-service",
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=dependencies,
    )
