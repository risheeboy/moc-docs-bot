"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, MagicMock
import asyncio

from app.main import app
from app.db.models import Base
from app.dependencies import get_db, get_redis
from app.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create in-memory test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_redis():
    """Mock Redis for testing."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_redis] = lambda: redis_mock
    return redis_mock


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        app_env="testing",
        app_debug=True,
        postgres_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
    )


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rag_response():
    """Mock RAG service response."""
    return {
        "context": "Test context",
        "sources": [
            {
                "title": "Test Document",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "score": 0.95,
                "source_site": "example.com",
                "language": "en",
                "content_type": "webpage",
                "chunk_id": "chunk_123",
            }
        ],
        "confidence": 0.85,
        "cached": False,
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM service response."""
    return {
        "id": "chatcmpl-123",
        "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Test response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }
