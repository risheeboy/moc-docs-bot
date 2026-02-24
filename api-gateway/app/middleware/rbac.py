"""Role-based access control (RBAC) middleware."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import os

logger = logging.getLogger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """Check JWT claims against role-based permissions."""

    # Define endpoint permissions by role
    ENDPOINT_PERMISSIONS = {
        "/api/v1/chat": ["api_consumer", "editor", "admin"],
        "/api/v1/chat/stream": ["api_consumer", "editor", "admin"],
        "/api/v1/search": ["api_consumer", "editor", "viewer", "admin"],
        "/api/v1/search/suggest": ["api_consumer", "editor", "viewer", "admin"],
        "/api/v1/voice/stt": ["api_consumer", "editor", "admin"],
        "/api/v1/voice/tts": ["api_consumer", "editor", "admin"],
        "/api/v1/translate": ["api_consumer", "editor", "admin"],
        "/api/v1/documents/upload": ["editor", "admin"],
        "/api/v1/documents": ["editor", "admin"],
        "/api/v1/feedback": ["api_consumer", "editor", "viewer", "admin"],
        "/api/v1/ocr/upload": ["editor", "admin"],
        "/api/v1/analytics": ["editor", "viewer", "admin"],
        "/api/v1/admin": ["admin"],
        "/api/v1/health": ["*"],  # Public
        "/api/v1/docs": ["*"],  # Public
        "/api/v1/redoc": ["*"],  # Public
        "/metrics": ["*"],  # Public
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check RBAC permissions before processing request."""
        path = request.url.path

        # Check if authentication is enabled (default: False for VPC-only access)
        auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() == "true"

        # If auth is disabled, treat all requests as admin
        if not auth_enabled:
            if not hasattr(request.state, "user"):
                request.state.user = {"role": "admin", "user_id": "vpc-internal"}
            return await call_next(request)

        # Check if endpoint requires authentication
        required_roles = self._get_required_roles(path)

        # Skip auth check for public endpoints
        if required_roles == ["*"]:
            return await call_next(request)

        # Extract role from request
        role = None
        if hasattr(request.state, "user"):
            role = request.state.user.get("role")
        elif hasattr(request.state, "api_key_user"):
            role = "api_consumer"

        # Check if user is authenticated and has required role
        if not role or role not in required_roles:
            logger.warning(
                f"RBAC denied access to {path} for role {role}",
                extra={"request_id": getattr(request.state, "request_id", "unknown")},
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Insufficient permissions",
                        "details": {"required_roles": required_roles, "user_role": role},
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    }
                },
            )

        return await call_next(request)

    def _get_required_roles(self, path: str) -> list[str]:
        """Get required roles for an endpoint."""
        # Check exact match first
        if path in self.ENDPOINT_PERMISSIONS:
            return self.ENDPOINT_PERMISSIONS[path]

        # Check prefix matches
        for endpoint_prefix, roles in self.ENDPOINT_PERMISSIONS.items():
            if path.startswith(endpoint_prefix):
                return roles

        # Default: allow for unknown endpoints
        return ["*"]
