"""Health check response models from §5 of Shared Contracts."""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DependencyHealth(BaseModel):
    """Health status of a service dependency."""

    status: str = Field(
        ...,
        description="healthy | degraded | unhealthy",
    )
    latency_ms: float = Field(..., description="Response latency in milliseconds")

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Standard health check response for all services."""

    status: str = Field(
        ...,
        description="Overall service status: healthy | degraded | unhealthy",
    )
    service: str = Field(..., description="Docker service name")
    version: str = Field(..., description="SemVer version string")
    uptime_seconds: float = Field(..., description="Seconds since service start")
    timestamp: datetime = Field(..., description="Current server time in ISO 8601 UTC")
    dependencies: dict[str, DependencyHealth] = Field(
        default_factory=dict,
        description="Map of dependency name to health status",
    )

    model_config = ConfigDict(from_attributes=True)

    def to_http_status_code(self) -> int:
        """Map health status to HTTP status code."""
        if self.status == "healthy":
            return 200
        elif self.status == "degraded":
            return 200  # Still OK
        else:  # unhealthy
            return 503
