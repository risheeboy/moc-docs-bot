"""Health check endpoint for Speech Service"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import time
import torch
import psutil

from app.config import config
from app.services.indic_conformer_stt import get_stt_model
from app.services.indic_tts import get_hindi_tts_model
from app.services.coqui_tts import get_english_tts_model

logger = logging.getLogger(__name__)
router = APIRouter()

# Service start time (for uptime calculation)
SERVICE_START_TIME = time.time()


class DependencyHealth(BaseModel):
    """Health status of a dependency"""

    status: str = Field(
        ..., description="healthy, degraded, or unhealthy"
    )
    latency_ms: float = Field(..., description="Response time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response format (from shared contracts §5)"""

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    service: str = Field(default="speech-service")
    version: str = Field(default=config.version)
    uptime_seconds: float = Field(..., description="Seconds since service started")
    timestamp: datetime = Field(
        ..., description="Current server time in ISO 8601 UTC"
    )
    dependencies: dict[str, DependencyHealth] = Field(
        ..., description="Dependency health statuses"
    )


def check_gpu_availability() -> tuple[bool, float]:
    """Check if GPU is available and get memory usage"""
    try:
        if torch.cuda.is_available():
            latency = 0.0
            return True, latency
        return False, 0.0
    except Exception as e:
        logger.error(f"GPU check failed: {e}")
        return False, 0.0


def check_models_loaded() -> dict[str, bool]:
    """Check if all required models are loaded"""
    return {
        "stt_model": get_stt_model().check_model_loaded(),
        "hindi_tts_model": get_hindi_tts_model().check_model_loaded(),
        "english_tts_model": get_english_tts_model().check_model_loaded(),
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns service status and dependency health information.
    Format specified in shared contracts §5.
    """
    try:
        start_time = time.time()

        # Calculate uptime
        uptime_seconds = time.time() - SERVICE_START_TIME

        # Check GPU availability
        gpu_available, gpu_latency = check_gpu_availability()

        # Check model loading
        models_status = check_models_loaded()

        # Overall status determination
        dependencies = {}

        # GPU status
        if gpu_available:
            dependencies["gpu"] = DependencyHealth(
                status="healthy", latency_ms=gpu_latency
            )
        else:
            dependencies["gpu"] = DependencyHealth(
                status="degraded", latency_ms=0.0
            )
            logger.warning("GPU not available - will use CPU (slower inference)")

        # Models status
        all_models_loaded = all(models_status.values())
        if all_models_loaded:
            dependencies["models"] = DependencyHealth(
                status="healthy", latency_ms=0.0
            )
        else:
            missing_models = [k for k, v in models_status.items() if not v]
            logger.warning(f"Some models not loaded: {missing_models}")
            dependencies["models"] = DependencyHealth(
                status="degraded", latency_ms=0.0
            )

        # CPU and memory
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem_percent = psutil.virtual_memory().percent

            if cpu_percent < 90 and mem_percent < 90:
                dependencies["memory"] = DependencyHealth(
                    status="healthy", latency_ms=0.0
                )
            else:
                dependencies["memory"] = DependencyHealth(
                    status="degraded", latency_ms=0.0
                )
                logger.warning(f"High resource usage: CPU {cpu_percent}%, Mem {mem_percent}%")
        except Exception as e:
            logger.error(f"Failed to check system resources: {e}")
            dependencies["memory"] = DependencyHealth(
                status="unknown", latency_ms=0.0
            )

        # Determine overall status
        if all_models_loaded and gpu_available:
            overall_status = "healthy"
        elif all_models_loaded:
            overall_status = "degraded"  # Models loaded but GPU not available
        else:
            overall_status = "unhealthy"  # Models not loaded

        response = HealthResponse(
            status=overall_status,
            service="speech-service",
            version=config.version,
            uptime_seconds=uptime_seconds,
            timestamp=datetime.utcnow(),
            dependencies=dependencies,
        )

        # Return appropriate HTTP status
        if overall_status == "unhealthy":
            raise HTTPException(status_code=503, detail=response.model_dump())

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Health check failed",
                    "details": {"error": str(e)},
                }
            },
        )
