"""Error response models from §4 of Shared Contracts."""

from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ErrorDetail(BaseModel):
    """Error detail with machine and human-readable messages."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="UUID v4 for request tracing",
    )

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    error: ErrorDetail

    model_config = ConfigDict(from_attributes=True)


# Standard error codes and HTTP status mappings (for reference)
ERROR_CODES = {
    "INVALID_REQUEST": 400,
    "INVALID_LANGUAGE": 400,
    "INVALID_AUDIO_FORMAT": 400,
    "UNAUTHORIZED": 401,
    "TOKEN_EXPIRED": 401,
    "FORBIDDEN": 403,
    "API_KEY_REVOKED": 403,
    "NOT_FOUND": 404,
    "DUPLICATE": 409,
    "PAYLOAD_TOO_LARGE": 413,
    "PROCESSING_FAILED": 422,
    "RATE_LIMIT_EXCEEDED": 429,
    "INTERNAL_ERROR": 500,
    "UPSTREAM_ERROR": 502,
    "SERVICE_UNAVAILABLE": 503,
    "MODEL_LOADING": 503,
    "UPSTREAM_TIMEOUT": 504,
}
