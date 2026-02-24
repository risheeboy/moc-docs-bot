"""Health check router for LLM Service

Exposes GET /health endpoint with per-model status information.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.services.model_manager import ModelManager
from app.models.health import HealthResponse, DependencyHealth

logger = logging.getLogger(__name__)
router = APIRouter()

# Track service start time
_service_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(model_manager: ModelManager = None) -> HealthResponse:
    """
    Health check endpoint reporting service and per-model status.

    Returns:
        HealthResponse with overall status and per-model loaded state
    """
    try:
        if model_manager is None:
            # This would be injected by FastAPI dependency
            from app.main import get_model_manager
            model_manager = get_model_manager()

        uptime_seconds = time.time() - _service_start_time

        # Check model statuses
        dependencies: Dict[str, DependencyHealth] = {}

        # Standard model
        start = time.time()
        standard_loaded = model_manager.is_model_loaded("standard")
        latency_ms = (time.time() - start) * 1000
        dependencies["llm_standard"] = DependencyHealth(
            status="healthy" if standard_loaded else "unhealthy",
            latency_ms=latency_ms
        )

        # Long context model
        start = time.time()
        longctx_loaded = model_manager.is_model_loaded("longctx")
        latency_ms = (time.time() - start) * 1000
        dependencies["llm_longctx"] = DependencyHealth(
            status="healthy" if longctx_loaded else "unhealthy",
            latency_ms=latency_ms
        )

        # Multimodal model
        start = time.time()
        multimodal_loaded = model_manager.is_model_loaded("multimodal")
        latency_ms = (time.time() - start) * 1000
        dependencies["llm_multimodal"] = DependencyHealth(
            status="healthy" if multimodal_loaded else "unhealthy",
            latency_ms=latency_ms
        )

        # Determine overall status
        all_healthy = standard_loaded and longctx_loaded and multimodal_loaded
        any_healthy = standard_loaded or longctx_loaded or multimodal_loaded

        if all_healthy:
            overall_status = "healthy"
            http_status = status.HTTP_200_OK
        elif any_healthy:
            overall_status = "degraded"
            http_status = status.HTTP_200_OK
        else:
            overall_status = "unhealthy"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        response = HealthResponse(
            status=overall_status,
            service="llm-service",
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            timestamp=datetime.utcnow(),
            dependencies=dependencies
        )

        if http_status != status.HTTP_200_OK:
            raise HTTPException(status_code=http_status, detail=response.model_dump())

        return response

    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Health check failed",
                    "details": {"error": str(e)}
                }
            }
        )
