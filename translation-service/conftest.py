"""Pytest configuration and fixtures for Translation Service tests"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.indictrans2_engine import indictrans2_engine
from app.services.cache import translation_cache


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def mock_indictrans2_init():
    """Mock IndicTrans2 initialization for all tests"""
    with patch.object(indictrans2_engine, "_initialized", True):
        with patch.object(indictrans2_engine, "model", AsyncMock()):
            with patch.object(indictrans2_engine, "tokenizer", AsyncMock()):
                yield


@pytest.fixture(autouse=True)
async def mock_redis_cache():
    """Mock Redis cache for all tests"""
    with patch.object(translation_cache, "_connected", True):
        with patch.object(translation_cache, "redis", AsyncMock()):
            yield
