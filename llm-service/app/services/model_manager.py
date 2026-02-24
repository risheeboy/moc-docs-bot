"""Model Manager for vLLM multi-model serving

Handles loading, unloading, and lifecycle management of multiple LLM models
with GPU memory optimization and LRU eviction.
"""

import asyncio
import logging
from typing import Dict, Optional, Tuple
from vllm import AsyncLLMEngine, EngineArgs
from app.config import LLMConfig

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages multi-model LLM inference with vLLM"""

    def __init__(self, config: LLMConfig):
        """Initialize model manager

        Args:
            config: LLM configuration
        """
        self.config = config
        self.models: Dict[str, AsyncLLMEngine] = {}
        self.model_loaded: Dict[str, bool] = {
            "standard": False,
            "longctx": False,
            "multimodal": False
        }
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize and preload configured models"""
        try:
            preload_list = self.config.llm_preload_models.split(",")
            preload_list = [m.strip() for m in preload_list]

            for model_key in preload_list:
                if model_key in self.model_loaded:
                    logger.info(f"Preloading model: {model_key}")
                    await self.load_model(model_key)

        except Exception as e:
            logger.error("Model initialization failed", exc_info=True)
            raise

    async def load_model(self, model_key: str) -> bool:
        """Load a model into GPU memory

        Args:
            model_key: "standard", "longctx", or "multimodal"

        Returns:
            True if model loaded successfully
        """
        async with self._lock:
            if self.model_loaded.get(model_key, False):
                return True

            try:
                model_id = self._get_model_id(model_key)
                max_model_len = self._get_max_model_len(model_key)

                logger.info(
                    "Loading model",
                    extra={
                        "model_key": model_key,
                        "model_id": model_id,
                        "max_model_len": max_model_len
                    }
                )

                # Create engine args
                engine_args = EngineArgs(
                    model=model_id,
                    max_model_len=max_model_len,
                    gpu_memory_utilization=self.config.llm_gpu_memory_utilization,
                    dtype="auto",
                    quantization="awq",
                    tensor_parallel_size=self.config.llm_tensor_parallel_size,
                    pipeline_parallel_size=self.config.llm_pipeline_parallel_size,
                    disable_log_requests=False,
                    enable_prefix_caching=True,
                    swap_space=4,
                    cpu_offload_gb=4
                )

                # Create engine
                engine = AsyncLLMEngine.from_engine_args(engine_args)
                self.models[model_key] = engine
                self.model_loaded[model_key] = True

                logger.info(
                    "Model loaded successfully",
                    extra={"model_key": model_key}
                )
                return True

            except Exception as e:
                logger.error(
                    "Failed to load model",
                    exc_info=True,
                    extra={"model_key": model_key}
                )
                self.model_loaded[model_key] = False
                raise

    async def unload_model(self, model_key: str) -> bool:
        """Unload a model from GPU memory

        Args:
            model_key: "standard", "longctx", or "multimodal"

        Returns:
            True if model unloaded successfully
        """
        async with self._lock:
            if model_key not in self.models:
                return True

            try:
                logger.info(f"Unloading model: {model_key}")

                engine = self.models[model_key]
                await engine.abort_request(model_key)
                del self.models[model_key]
                self.model_loaded[model_key] = False

                logger.info(f"Model unloaded: {model_key}")
                return True

            except Exception as e:
                logger.error(
                    "Failed to unload model",
                    exc_info=True,
                    extra={"model_key": model_key}
                )
                return False

    def is_model_loaded(self, model_key: str) -> bool:
        """Check if a model is currently loaded

        Args:
            model_key: "standard", "longctx", or "multimodal"

        Returns:
            True if model is loaded
        """
        return self.model_loaded.get(model_key, False)

    def get_engine(self, model_key: str) -> Optional[AsyncLLMEngine]:
        """Get vLLM engine for a model

        Args:
            model_key: "standard", "longctx", or "multimodal"

        Returns:
            AsyncLLMEngine or None if not loaded
        """
        if not self.is_model_loaded(model_key):
            return None
        return self.models.get(model_key)

    def _get_model_id(self, model_key: str) -> str:
        """Get HuggingFace model ID for model key"""
        if model_key == "standard":
            return self.config.llm_model_standard
        elif model_key == "longctx":
            return self.config.llm_model_longctx
        elif model_key == "multimodal":
            return self.config.llm_model_multimodal
        else:
            return self.config.llm_model_standard

    def _get_max_model_len(self, model_key: str) -> int:
        """Get max model length for model key"""
        if model_key == "standard":
            return self.config.llm_max_model_len_standard
        elif model_key == "longctx":
            return self.config.llm_max_model_len_longctx
        elif model_key == "multimodal":
            return self.config.llm_max_model_len_multimodal
        else:
            return self.config.llm_max_model_len_standard

    async def shutdown(self):
        """Shutdown all models"""
        try:
            for model_key in list(self.models.keys()):
                await self.unload_model(model_key)
            logger.info("Model manager shutdown complete")
        except Exception as e:
            logger.error("Error during model manager shutdown", exc_info=True)
