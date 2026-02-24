"""Async PostgreSQL client helper."""

from typing import Any, Optional
import asyncpg
from asyncpg import Connection, Pool
import logging

logger = logging.getLogger(__name__)


class PostgresClient:
    """Helper for async PostgreSQL connections."""

    def __init__(self, dsn: str, min_size: int = 5, max_size: int = 20):
        """Initialize PostgreSQL client.

        Args:
            dsn: Database connection string
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[Pool] = None

    async def connect(self) -> None:
        """Create connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=60,
            )
            logger.info(f"Connected to PostgreSQL (pool: {self.min_size}-{self.max_size})")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL")

    async def execute(self, query: str, *args: Any) -> str:
        """Execute query without returning results.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Command status string
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Fetch all rows from query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        """Fetch single row from query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Fetch single value from query.

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def transaction(self) -> Any:
        """Get a transaction context for multiple operations.

        Returns:
            Transaction context manager
        """
        if not self.pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self.pool.acquire() as conn:
            return conn.transaction()

    async def health_check(self) -> bool:
        """Check PostgreSQL connection health.

        Returns:
            True if database is healthy
        """
        try:
            if self.pool:
                await self.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        return False

    async def __aenter__(self) -> "PostgresClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()
