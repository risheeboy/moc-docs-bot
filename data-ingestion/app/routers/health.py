"""Health check endpoint for Data Ingestion Service."""

import structlog
import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()
router = APIRouter()

# Track service start time
_start_time = time.time()


class DependencyHealth(BaseModel):
    """Dependency health status."""
    status: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: datetime
    dependencies: Dict[str, DependencyHealth]


async def check_minio_health() -> tuple[str, float]:
    """Check MinIO connectivity."""
    import time
    try:
        from minio import Minio

        start = time.time()
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        # Try to list buckets
        client.list_buckets()
        latency_ms = (time.time() - start) * 1000
        return "healthy", latency_ms
    except Exception as e:
        logger.warning("minio_health_check_failed", error=str(e))
        return "unhealthy", 0.0


async def check_postgres_health() -> tuple[str, float]:
    """Check PostgreSQL connectivity."""
    import time
    try:
        import asyncpg

        start = time.time()
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            timeout=5,
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        latency_ms = (time.time() - start) * 1000
        return "healthy", latency_ms
    except Exception as e:
        logger.warning("postgres_health_check_failed", error=str(e))
        return "unhealthy", 0.0


async def check_redis_health() -> tuple[str, float]:
    """Check Redis connectivity."""
    import time
    try:
        import redis.asyncio as redis

        start = time.time()
        r = redis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db_cache}",
            password=settings.redis_password,
            decode_responses=True,
        )
        await r.ping()
        await r.close()
        latency_ms = (time.time() - start) * 1000
        return "healthy", latency_ms
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        return "unhealthy", 0.0


async def check_rag_service_health() -> tuple[str, float]:
    """Check RAG Service connectivity."""
    import time
    import httpx

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.rag_service_url}/health")
            response.raise_for_status()
        latency_ms = (time.time() - start) * 1000
        return "healthy", latency_ms
    except Exception as e:
        logger.warning("rag_service_health_check_failed", error=str(e))
        return "degraded", 0.0  # RAG service is not critical for ingestion


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Health check endpoint."""
    # Check all dependencies
    minio_status, minio_latency = await check_minio_health()
    postgres_status, postgres_latency = await check_postgres_health()
    redis_status, redis_latency = await check_redis_health()
    rag_status, rag_latency = await check_rag_service_health()

    # Determine overall status
    critical_healthy = minio_status == "healthy" and postgres_status == "healthy"

    if critical_healthy:
        overall_status = "healthy"
    elif minio_status == "healthy" or postgres_status == "healthy":
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    uptime = time.time() - _start_time

    return HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.service_version,
        uptime_seconds=uptime,
        timestamp=datetime.utcnow(),
        dependencies={
            "minio": DependencyHealth(status=minio_status, latency_ms=minio_latency),
            "postgres": DependencyHealth(
                status=postgres_status, latency_ms=postgres_latency
            ),
            "redis": DependencyHealth(status=redis_status, latency_ms=redis_latency),
            "rag_service": DependencyHealth(
                status=rag_status, latency_ms=rag_latency
            ),
        },
    )
