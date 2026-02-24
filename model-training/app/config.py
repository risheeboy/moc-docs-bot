"""Configuration for the model training service."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class TrainingConfig(BaseSettings):
    """Training hyperparameters and environment configuration."""

    # Service Configuration
    APP_ENV: str = os.getenv("APP_ENV", "production")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "INFO")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "")
    SERVICE_NAME: str = "model-training"
    SERVICE_VERSION: str = "1.0.0"

    # Training Hyperparameters
    TRAINING_LORA_RANK: int = int(os.getenv("TRAINING_LORA_RANK", "16"))
    TRAINING_LORA_ALPHA: int = int(os.getenv("TRAINING_LORA_ALPHA", "32"))
    TRAINING_LEARNING_RATE: float = float(os.getenv("TRAINING_LEARNING_RATE", "2e-4"))
    TRAINING_EPOCHS: int = int(os.getenv("TRAINING_EPOCHS", "3"))
    TRAINING_BATCH_SIZE: int = int(os.getenv("TRAINING_BATCH_SIZE", "4"))
    TRAINING_MAX_SEQ_LENGTH: int = int(os.getenv("TRAINING_MAX_SEQ_LENGTH", "2048"))
    TRAINING_WARMUP_RATIO: float = float(os.getenv("TRAINING_WARMUP_RATIO", "0.1"))
    TRAINING_WEIGHT_DECAY: float = float(os.getenv("TRAINING_WEIGHT_DECAY", "0.01"))
    TRAINING_GRADIENT_ACCUMULATION_STEPS: int = int(os.getenv("TRAINING_GRADIENT_ACCUMULATION_STEPS", "4"))
    TRAINING_MAX_GRAD_NORM: float = float(os.getenv("TRAINING_MAX_GRAD_NORM", "1.0"))

    # Model Configuration
    LLM_MODEL_STANDARD: str = os.getenv("LLM_MODEL_STANDARD", "meta-llama/Llama-3.1-8B-Instruct-AWQ")
    LLM_MODEL_LONGCTX: str = os.getenv("LLM_MODEL_LONGCTX", "mistralai/Mistral-NeMo-Instruct-2407-AWQ")
    LLM_MODEL_MULTIMODAL: str = os.getenv("LLM_MODEL_MULTIMODAL", "google/gemma-3-12b-it-awq")
    LLM_GPU_MEMORY_UTILIZATION: float = float(os.getenv("LLM_GPU_MEMORY_UTILIZATION", "0.85"))

    # MinIO Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET_MODELS: str = os.getenv("MINIO_BUCKET_MODELS", "models")
    MINIO_BUCKET_DOCUMENTS: str = os.getenv("MINIO_BUCKET_DOCUMENTS", "documents")
    MINIO_USE_SSL: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB_CACHE: int = int(os.getenv("REDIS_DB_CACHE", "0"))
    REDIS_DB_SESSION: int = int(os.getenv("REDIS_DB_SESSION", "2"))

    # PostgreSQL Configuration (for metadata)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ragqa")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ragqa_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # GPU Configuration
    CUDA_VISIBLE_DEVICES: str = os.getenv("CUDA_VISIBLE_DEVICES", "0")
    NVIDIA_DRIVER_MIN_VERSION: str = os.getenv("NVIDIA_DRIVER_MIN_VERSION", "535")
    CUDA_MIN_VERSION: str = os.getenv("CUDA_MIN_VERSION", "12.1")

    # Data Configuration
    DATA_TRAIN_DIR: str = "/app/data/train"
    DATA_EVAL_DIR: str = "/app/data/eval"
    DATA_QA_PAIRS_PATH: str = "/app/data/ministry_qa_pairs.jsonl"
    EVAL_DATASET_SIZE: int = int(os.getenv("EVAL_DATASET_SIZE", "500"))

    # Job Configuration
    MAX_CONCURRENT_TRAINING_JOBS: int = int(os.getenv("MAX_CONCURRENT_TRAINING_JOBS", "1"))
    JOB_TIMEOUT_SECONDS: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "86400"))  # 24 hours
    JOB_POLL_INTERVAL_SECONDS: int = int(os.getenv("JOB_POLL_INTERVAL_SECONDS", "5"))

    # Evaluation Configuration
    EVAL_METRICS: list = ["exact_match", "f1", "bleu", "ndcg", "hallucination_rate", "llm_judge_score"]
    HALLUCINATION_THRESHOLD: float = float(os.getenv("HALLUCINATION_THRESHOLD", "0.15"))
    EVALUATION_MODEL: str = os.getenv("EVALUATION_MODEL", "meta-llama/Llama-3.1-8B-Instruct-AWQ")

    # LLM Service Configuration
    LLM_SERVICE_URL: str = os.getenv("LLM_SERVICE_URL", "http://llm-service:8002")

    # Continuous Learning
    FEEDBACK_COLLECTION_ENABLED: bool = os.getenv("FEEDBACK_COLLECTION_ENABLED", "true").lower() == "true"
    RETRAIN_TRIGGER_THRESHOLD: int = int(os.getenv("RETRAIN_TRIGGER_THRESHOLD", "100"))
    DATA_DRIFT_WINDOW_DAYS: int = int(os.getenv("DATA_DRIFT_WINDOW_DAYS", "30"))
    RETRAIN_SCHEDULE_INTERVAL_HOURS: int = int(os.getenv("RETRAIN_SCHEDULE_INTERVAL_HOURS", "168"))  # 1 week

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_config() -> TrainingConfig:
    """Get the global configuration instance."""
    return TrainingConfig()
