"""Redis-based token bucket rate limiting middleware."""

import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from redis.asyncio import Redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiting per role."""

    def __init__(self, app, redis: Redis, rate_limits: dict[str, int]):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI app
            redis: Redis client
            rate_limits: Dict mapping role -> requests_per_minute
        """
        super().__init__(app)
        self.redis = redis
        self.rate_limits = rate_limits

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limit before processing request."""
        # Skip rate limiting for health checks and public endpoints
        if request.url.path in ["/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/metrics"]:
            return await call_next(request)

        # Extract user identity and role
        user_id = None
        role = "api_consumer"  # default

        # Try to get user info from request
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("user_id")
            role = request.state.user.get("role", "api_consumer")
        elif hasattr(request.state, "api_key_user"):
            user_id = request.state.api_key_user.get("user_id")
            role = "api_consumer"

        if not user_id:
            # Use IP address as fallback
            user_id = request.client.host if request.client else "unknown"

        # Get rate limit for role
        limit = self.rate_limits.get(role, 60)
        limit_per_second = limit / 60.0

        # Rate limit key in Redis
        key = f"rate_limit:{user_id}:{role}"

        try:
            # Implement token bucket algorithm
            current = await self.redis.get(key)
            if current is None:
                tokens = limit
                await self.redis.setex(key, 60, int(limit))
            else:
                tokens = int(current)

            if tokens > 0:
                # Consume one token
                await self.redis.decr(key)
            else:
                # Rate limit exceeded
                logger.warning(f"Rate limit exceeded for {user_id} with role {role}")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit of {limit} requests per minute exceeded",
                            "details": {"role": role, "limit": limit},
                            "request_id": getattr(request.state, "request_id", "unknown"),
                        }
                    },
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Don't block on rate limiter failure
            pass

        response = await call_next(request)
        return response
