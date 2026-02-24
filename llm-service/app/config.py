"""Configuration module for LLM Service

Reads environment variables for model selection, GPU allocation, and service parameters.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM Service configuration from environment variables"""

    # Service settings
    app_env: str = os.getenv("APP_ENV", "production")
    app_debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    app_log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")

    # Model configurations
    llm_model_standard: str = os.getenv(
        "LLM_MODEL_STANDARD",
        "meta-llama/Llama-3.1-8B-Instruct-AWQ"
    )
    llm_model_longctx: str = os.getenv(
        "LLM_MODEL_LONGCTX",
        "mistralai/Mistral-NeMo-Instruct-2407-AWQ"
    )
    llm_model_multimodal: str = os.getenv(
        "LLM_MODEL_MULTIMODAL",
        "google/gemma-3-12b-it-awq"
    )

    # GPU settings
    llm_gpu_memory_utilization: float = float(
        os.getenv("LLM_GPU_MEMORY_UTILIZATION", "0.85")
    )
    llm_max_model_len_standard: int = int(
        os.getenv("LLM_MAX_MODEL_LEN_STANDARD", "8192")
    )
    llm_max_model_len_longctx: int = int(
        os.getenv("LLM_MAX_MODEL_LEN_LONGCTX", "131072")
    )
    llm_max_model_len_multimodal: int = int(
        os.getenv("LLM_MAX_MODEL_LEN_MULTIMODAL", "8192")
    )

    # Inference settings
    llm_tensor_parallel_size: int = int(
        os.getenv("LLM_TENSOR_PARALLEL_SIZE", "1")
    )
    llm_pipeline_parallel_size: int = int(
        os.getenv("LLM_PIPELINE_PARALLEL_SIZE", "1")
    )

    # Service settings
    service_port: int = 8002
    service_host: str = "0.0.0.0"

    # Langfuse integration
    langfuse_enabled: bool = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "http://langfuse:3001")
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")

    # Model loading settings
    llm_load_on_startup: bool = os.getenv("LLM_LOAD_ON_STARTUP", "true").lower() == "true"
    llm_preload_models: str = os.getenv("LLM_PRELOAD_MODELS", "standard")  # comma-separated

    # Cache settings
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db_cache: int = int(os.getenv("REDIS_DB_CACHE", "0"))

    # Inference defaults
    llm_default_temperature: float = 0.3
    llm_default_max_tokens: int = 1024
    llm_default_top_p: float = 0.95
    llm_default_top_k: int = 40

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> LLMConfig:
    """Get LLM configuration singleton"""
    return LLMConfig()
