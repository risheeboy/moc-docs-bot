"""Shared dependencies for FastAPI."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from .config import get_settings, Settings
from .db.connection import Database
from .auth.jwt_handler import JWTHandler
from .auth.api_key import APIKeyManager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global instances
_db: Optional[Database] = None
_redis: Optional[Redis] = None
_jwt_handler: Optional[JWTHandler] = None


async def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


async def get_db(settings: Settings = Depends(get_settings_dep)) -> AsyncSession:
    """Get database session."""
    global _db
    if _db is None:
        _db = Database(settings.postgres_url)
        await _db.initialize()

    async with _db.async_session() as session:
        yield session


async def get_redis(settings: Settings = Depends(get_settings_dep)) -> Redis:
    """Get Redis connection."""
    global _redis
    if _redis is None:
        _redis = await Redis.from_url(settings.redis_url, decode_responses=True)

    return _redis


async def get_jwt_handler(settings: Settings = Depends(get_settings_dep)) -> JWTHandler:
    """Get JWT handler."""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        )
    return _jwt_handler


async def verify_jwt_token(request: Request, jwt_handler: JWTHandler = Depends(get_jwt_handler)):
    """Verify JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        # Check if it's a public endpoint
        if request.url.path in ["/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/metrics"]:
            return None
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = auth_header.split(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = jwt_handler.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        request.state.user = {
            "user_id": payload.user_id,
            "email": payload.email,
            "role": payload.role,
        }
        return payload
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


async def verify_api_key(
    request: Request, db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)
):
    """Verify API key from X-API-Key header."""
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        # Check if it's a public endpoint
        if request.url.path in ["/api/v1/health", "/api/v1/docs", "/api/v1/redoc", "/metrics"]:
            return None
        raise HTTPException(status_code=401, detail="Missing API key")

    try:
        from .db.crud import APIKeyCRUD

        key_hash = APIKeyManager.hash_key(api_key)
        key_record = await APIKeyCRUD.get_by_hash(db, key_hash)

        if not key_record or not key_record.active:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")

        # Update last used
        await APIKeyCRUD.update_last_used(db, key_record.key_id)

        request.state.api_key_user = {
            "user_id": key_record.user_id,
            "role": key_record.role,
        }
        return key_record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        raise HTTPException(status_code=401, detail="API key verification failed")


async def get_current_user(request: Request):
    """Get current user from request state."""
    if hasattr(request.state, "user"):
        return request.state.user
    if hasattr(request.state, "api_key_user"):
        return request.state.api_key_user
    raise HTTPException(status_code=401, detail="Not authenticated")
