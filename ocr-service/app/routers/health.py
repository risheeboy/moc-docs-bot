"""Health check router."""

import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

logger = structlog.get_logger()

# Service startup time
_startup_time = time.time()


class DependencyHealth(BaseModel):
    """Health status of a dependency."""

    status: str = Field(..., description="healthy | degraded | unhealthy")
    latency_ms: float = Field(..., description="Latency in milliseconds")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Seconds since startup")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    dependencies: dict[str, DependencyHealth] = Field(
        ..., description="Dependency health status"
    )


router = APIRouter()


async def check_tesseract_health() -> Optional[DependencyHealth]:
    """Check Tesseract OCR engine health."""
    try:
        import pytesseract
        from PIL import Image
        import io

        start = time.time()

        # Test with a simple 1x1 white image
        test_image = Image.new("RGB", (1, 1), color="white")
        pytesseract.image_to_string(test_image)

        latency = (time.time() - start) * 1000
        return DependencyHealth(status="healthy", latency_ms=latency)
    except Exception as e:
        logger.warning("tesseract_health_check_failed", error=str(e))
        return DependencyHealth(status="degraded", latency_ms=0)


async def check_easyocr_health() -> Optional[DependencyHealth]:
    """Check EasyOCR engine health."""
    try:
        # EasyOCR initialization is expensive, just check if module loads
        start = time.time()
        import easyocr  # noqa: F401

        latency = (time.time() - start) * 1000
        return DependencyHealth(status="healthy", latency_ms=latency)
    except Exception as e:
        logger.warning("easyocr_health_check_failed", error=str(e))
        return DependencyHealth(status="degraded", latency_ms=0)


@router.get("", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns the overall service health and dependency status.
    """
    from app.config import settings

    request_id = getattr(request.state, "request_id", "unknown")

    # Check dependency health
    tesseract_health = await check_tesseract_health()
    easyocr_health = await check_easyocr_health()

    dependencies = {
        "tesseract": tesseract_health or DependencyHealth(status="unhealthy", latency_ms=0),
        "easyocr": easyocr_health or DependencyHealth(status="unhealthy", latency_ms=0),
    }

    # Determine overall status
    all_statuses = [dep.status for dep in dependencies.values()]
    if all(s == "healthy" for s in all_statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in all_statuses):
        overall_status = "degraded"
    else:
        overall_status = "degraded"

    uptime_seconds = time.time() - _startup_time
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    response = HealthResponse(
        status=overall_status,
        service=settings.service_name,
        version=settings.version,
        uptime_seconds=uptime_seconds,
        timestamp=timestamp,
        dependencies=dependencies,
    )

    logger.info(
        "health_check",
        status=overall_status,
        uptime_seconds=uptime_seconds,
        request_id=request_id,
    )

    return response
