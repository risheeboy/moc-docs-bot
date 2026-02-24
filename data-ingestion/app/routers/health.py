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


async def check_s3_health() -> tuple[str, float]:
    """Check S3 connectivity."""
    import time
    try:
        import boto3

        start = time.time()
        client = boto3.client(
            "s3",
            region_name=settings.aws_default_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        # Try to list buckets
        client.list_buckets()
        latency_ms = (time.time() - start) * 1000
        return "healthy", latency_ms
    except Exception as e:
        logger.warning("s3_health_check_failed", error=str(e))
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
    s3_status, s3_latency = await check_s3_health()
    postgres_status, postgres_latency = await check_postgres_health()
    redis_status, redis_latency = await check_redis_health()
    rag_status, rag_latency = await check_rag_service_health()

    # Determine overall status
    critical_healthy = s3_status == "healthy" and postgres_status == "healthy"

    if critical_healthy:
        overall_status = "healthy"
    elif s3_status == "healthy" or postgres_status == "healthy":
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
            "s3": DependencyHealth(status=s3_status, latency_ms=s3_latency),
            "postgres": DependencyHealth(
                status=postgres_status, latency_ms=postgres_latency
            ),
            "redis": DependencyHealth(status=redis_status, latency_ms=redis_latency),
            "rag_service": DependencyHealth(
                status=rag_status, latency_ms=rag_latency
            ),
        },
    )
