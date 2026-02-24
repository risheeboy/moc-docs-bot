"""Health check endpoint."""

import time
from datetime import datetime
from typing import Dict, Any, Optional

import redis
from fastapi import APIRouter, Header

from app.config import get_config
from app.utils.logging_config import setup_json_logging

router = APIRouter()
logger = setup_json_logging("health")
config = get_config()

# Service startup time for uptime calculation
_start_time = time.time()


def check_gpu_availability() -> Dict[str, Any]:
    """Check GPU availability.

    Returns:
        GPU status dict
    """
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            return {
                "status": "healthy",
                "device_count": device_count,
                "latency_ms": 5,
            }
        else:
            return {
                "status": "unhealthy",
                "device_count": 0,
                "latency_ms": 5,
                "error": "CUDA not available",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": 5,
            "error": str(e),
        }


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity.

    Returns:
        Redis status dict
    """
    start = time.time()
    try:
        client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        client.ping()
        latency_ms = (time.time() - start) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }


def check_minio() -> Dict[str, Any]:
    """Check MinIO connectivity.

    Returns:
        MinIO status dict
    """
    start = time.time()
    try:
        from minio import Minio
        client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_USE_SSL,
        )
        # Try to list buckets
        client.list_buckets()
        latency_ms = (time.time() - start) * 1000
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "status": "unhealthy",
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
        }


@router.get("/health")
async def health_check(x_request_id: Optional[str] = Header(None)):
    """Get service health status.

    Returns:
        Health status response
    """
    # Check dependencies
    gpu_status = check_gpu_availability()
    redis_status = check_redis()
    minio_status = check_minio()

    # Determine overall status
    critical_deps = [gpu_status, minio_status]  # GPU and MinIO are critical
    non_critical_deps = [redis_status]

    critical_healthy = all(d["status"] != "unhealthy" for d in critical_deps)
    non_critical_healthy = all(d["status"] != "unhealthy" for d in non_critical_deps)

    if critical_healthy and non_critical_healthy:
        overall_status = "healthy"
        http_status = 200
    elif critical_healthy:
        overall_status = "degraded"
        http_status = 200
    else:
        overall_status = "unhealthy"
        http_status = 503

    uptime_seconds = time.time() - _start_time

    response = {
        "status": overall_status,
        "service": "model-training",
        "version": config.SERVICE_VERSION,
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {
            "gpu": gpu_status,
            "redis": redis_status,
            "minio": minio_status,
        },
    }

    return response


@router.get("/metrics")
async def metrics(x_request_id: Optional[str] = Header(None)):
    """Get Prometheus metrics.

    Returns:
        Prometheus-formatted metrics
    """
    from app.utils.metrics import get_metrics
    from fastapi.responses import Response

    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4",
    )
