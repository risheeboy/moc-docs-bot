"""Health check endpoint."""

from fastapi import APIRouter, Depends
from ..models import HealthResponse, DependencyHealth
from ..dependencies import get_db, get_redis
from ..config import get_settings
from datetime import datetime
import time
import logging

router = APIRouter(prefix="/api/v1", tags=["health"])
logger = logging.getLogger(__name__)

start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint for all dependencies."""
    uptime = time.time() - start_time
    dependencies = {}

    # Check PostgreSQL
    try:
        from ..db.connection import Database

        settings = get_settings()
        db = Database(settings.postgres_url)
        await db.initialize()
        is_healthy = await db.health_check()
        status = "healthy" if is_healthy else "unhealthy"
        dependencies["postgres"] = DependencyHealth(status=status, latency_ms=10)
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        dependencies["postgres"] = DependencyHealth(status="unhealthy", latency_ms=0)

    # Check Redis
    try:
        redis = None
        settings = get_settings()
        import redis as redis_lib

        redis = await redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
        pong = await redis.ping()
        status = "healthy" if pong else "unhealthy"
        dependencies["redis"] = DependencyHealth(status=status, latency_ms=5)
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        dependencies["redis"] = DependencyHealth(status="unhealthy", latency_ms=0)

    # Determine overall status
    overall_status = "healthy"
    for dep_status in dependencies.values():
        if dep_status.status == "unhealthy":
            overall_status = "unhealthy"
            break

    return HealthResponse(
        status=overall_status,
        service="api-gateway",
        version="1.0.0",
        uptime_seconds=uptime,
        timestamp=datetime.utcnow(),
        dependencies=dependencies,
    )
