import time
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.config import settings
from app.models.response import HealthResponse, DependencyHealth
from app.services.vector_store import VectorStoreService
from app.services.cache_service import CacheService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Track service startup time
_start_time = time.time()


@router.get("/health")
async def health_check() -> HealthResponse:
    """
    Health check endpoint that validates critical dependencies.

    Returns HTTP 503 if critical dependency (Milvus) is down.
    Returns HTTP 200 with 'degraded' if non-critical dependency (Redis) is down.
    """
    from app import __version__

    dependencies = {}
    overall_status = "healthy"

    # Check Milvus
    try:
        milvus_service = VectorStoreService()
        start = time.time()
        milvus_service._get_milvus_connection().get_collection_names()
        latency = (time.time() - start) * 1000
        dependencies["milvus"] = DependencyHealth(status="healthy", latency_ms=latency)
    except Exception as e:
        logger.error(f"Milvus health check failed: {e}")
        dependencies["milvus"] = DependencyHealth(status="unhealthy", latency_ms=0)
        overall_status = "unhealthy"

    # Check Redis
    try:
        cache_service = CacheService()
        start = time.time()
        cache_service.redis_client.ping()
        latency = (time.time() - start) * 1000
        dependencies["redis"] = DependencyHealth(status="healthy", latency_ms=latency)
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        dependencies["redis"] = DependencyHealth(status="unhealthy", latency_ms=0)
        if overall_status == "healthy":
            overall_status = "degraded"

    uptime = time.time() - _start_time

    response = HealthResponse(
        status=overall_status,
        service="rag-service",
        version=__version__,
        uptime_seconds=uptime,
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )

    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response.model_dump())

    return response
