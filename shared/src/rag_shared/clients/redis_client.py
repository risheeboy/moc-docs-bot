"""Redis client helper for cache and session management."""

from typing import Any, Optional
import redis.asyncio as redis
from redis.asyncio import Redis as RedisType
import json
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Helper for Redis connection and operations."""

    def __init__(self, redis_url: str, db: int = 0):
        """Initialize Redis client.

        Args:
            redis_url: Redis connection URL (redis://[:password]@host:port)
            db: Database number to select (default 0)
        """
        self.redis_url = redis_url
        self.db = db
        self.client: Optional[RedisType] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.client = await redis.from_url(self.redis_url, db=self.db, decode_responses=True)
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.redis_url} (db={self.db})")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.get(key)

    async def get_json(self, key: str) -> Optional[dict[str, Any]]:
        """Get and deserialize JSON from cache.

        Args:
            key: Cache key

        Returns:
            Deserialized object or None
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Failed to deserialize JSON from key {key}")
                return None
        return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (None for no expiry)
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        if ttl:
            await self.client.setex(key, ttl, value)
        else:
            await self.client.set(key, value)

    async def set_json(
        self,
        key: str,
        value: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Serialize and store JSON in cache.

        Args:
            key: Cache key
            value: Object to serialize
            ttl: Time to live in seconds
        """
        json_value = json.dumps(value)
        await self.set(key, json_value, ttl)

    async def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.exists(key) > 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.incrby(key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement numeric value.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.decrby(key, amount)

    async def get_ttl(self, key: str) -> int:
        """Get remaining time to live for key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds (-1 if no expiry, -2 if not found)
        """
        if not self.client:
            raise RuntimeError("Redis client not connected")
        return await self.client.ttl(key)

    async def health_check(self) -> bool:
        """Check Redis connection health.

        Returns:
            True if Redis is healthy
        """
        try:
            if self.client:
                await self.client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        return False

    async def __aenter__(self) -> "RedisClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
