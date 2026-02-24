"""Audit logging middleware."""

import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """Log all requests to audit trail (with PII sanitization)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request/response for audit."""
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # Extract relevant info from request
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Skip logging for non-critical endpoints
        if path in ["/metrics", "/health"]:
            return await call_next(request)

        # Get user info if available
        user_id = None
        role = "unknown"
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("user_id")
            role = request.state.user.get("role", "unknown")
        elif hasattr(request.state, "api_key_user"):
            user_id = request.state.api_key_user.get("user_id")
            role = "api_consumer"

        # Sanitize query params (remove sensitive data)
        sanitized_params = self._sanitize_params(query_params)

        # Process request
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Log audit entry
        try:
            logger.info(
                "api_request",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                user_id=user_id,
                role=role,
                query_params=sanitized_params,
            )
        except Exception as e:
            logger.error("audit_log_error", error=str(e), request_id=request_id)

        return response

    @staticmethod
    def _sanitize_params(params: dict) -> dict:
        """Remove PII from query parameters."""
        sensitive_keys = {
            "email",
            "phone",
            "aadhaar",
            "password",
            "token",
            "api_key",
            "secret",
        }

        sanitized = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized
