"""Redis-based caching service."""

import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheService:
    """Manage caching via Redis."""

    def __init__(self, redis: Redis):
        """Initialize cache service."""
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            await self.redis.setex(key, ttl_seconds, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_key(self, namespace: str, *parts: str) -> str:
        """Generate cache key from parts."""
        return f"{namespace}:{'_'.join(parts)}"
