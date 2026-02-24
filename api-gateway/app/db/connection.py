"""Database connection management."""

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging

logger = logging.getLogger(__name__)


class Database:
    """Manage database connections."""

    def __init__(self, database_url: str):
        """Initialize database."""
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        self.pool = None

    async def initialize(self):
        """Initialize database connections."""
        try:
            # SQLAlchemy async engine
            self.engine = create_async_engine(
                self.database_url, echo=False, pool_pre_ping=True
            )

            # Session factory
            self.async_session = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database closed")

    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        if not self.async_session:
            raise RuntimeError("Database not initialized")
        return self.async_session()

    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
