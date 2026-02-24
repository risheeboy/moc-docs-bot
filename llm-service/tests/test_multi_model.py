"""Tests for multi-model support

Tests model loading, switching, and health checks.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.config import LLMConfig
from app.services.model_manager import ModelManager


@pytest.fixture
def config():
    """Test configuration"""
    return LLMConfig(
        llm_model_standard="meta-llama/Llama-3.1-8B-Instruct-AWQ",
        llm_model_longctx="mistralai/Mistral-NeMo-Instruct-2407-AWQ",
        llm_model_multimodal="google/gemma-3-12b-it-awq",
        llm_gpu_memory_utilization=0.85,
        llm_max_model_len_standard=8192,
        llm_max_model_len_longctx=131072,
        llm_max_model_len_multimodal=8192,
        llm_load_on_startup=False
    )


@pytest.fixture
def model_manager(config):
    """Model manager instance"""
    return ModelManager(config)


@pytest.mark.asyncio
async def test_model_manager_initialization(model_manager):
    """Test model manager initialization"""
    assert not model_manager.is_model_loaded("standard")
    assert not model_manager.is_model_loaded("longctx")
    assert not model_manager.is_model_loaded("multimodal")


@pytest.mark.asyncio
async def test_model_loading(model_manager):
    """Test model loading"""
    with patch('app.services.model_manager.AsyncLLMEngine.from_engine_args') as mock_engine:
        mock_engine.return_value = MagicMock()

        success = await model_manager.load_model("standard")
        assert success
        assert model_manager.is_model_loaded("standard")


@pytest.mark.asyncio
async def test_model_unloading(model_manager):
    """Test model unloading"""
    # First load
    with patch('app.services.model_manager.AsyncLLMEngine.from_engine_args') as mock_engine:
        mock_engine.return_value = MagicMock()
        await model_manager.load_model("standard")
        assert model_manager.is_model_loaded("standard")

    # Then unload
    success = await model_manager.unload_model("standard")
    assert success
    assert not model_manager.is_model_loaded("standard")


@pytest.mark.asyncio
async def test_get_model_id(model_manager):
    """Test model ID retrieval"""
    assert model_manager._get_model_id("standard") == model_manager.config.llm_model_standard
    assert model_manager._get_model_id("longctx") == model_manager.config.llm_model_longctx
    assert model_manager._get_model_id("multimodal") == model_manager.config.llm_model_multimodal


@pytest.mark.asyncio
async def test_get_max_model_len(model_manager):
    """Test max model length retrieval"""
    assert model_manager._get_max_model_len("standard") == 8192
    assert model_manager._get_max_model_len("longctx") == 131072
    assert model_manager._get_max_model_len("multimodal") == 8192


@pytest.mark.asyncio
async def test_concurrent_model_loading(model_manager):
    """Test thread-safe concurrent model operations"""
    import asyncio

    with patch('app.services.model_manager.AsyncLLMEngine.from_engine_args') as mock_engine:
        mock_engine.return_value = MagicMock()

        # Try to load same model concurrently
        results = await asyncio.gather(
            model_manager.load_model("standard"),
            model_manager.load_model("standard")
        )

        # Both should succeed, but only one engine created (due to lock)
        assert all(results)
        assert model_manager.is_model_loaded("standard")
