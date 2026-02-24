"""
Shared configuration loader using Pydantic Settings.

Reads all environment variables from §3.2 of Shared Contracts.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-level settings."""

    env: str = "production"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        env_file=".env",
    )


class PostgresSettings(BaseSettings):
    """Main PostgreSQL (ragqa) settings."""

    host: str = "postgres"
    port: int = 5432
    db: str = "ragqa"
    user: str = "ragqa_user"
    password: str

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        case_sensitive=False,
        env_file=".env",
    )

    @property
    def dsn(self) -> str:
        """Construct PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class LangfusePostgresSettings(BaseSettings):
    """Langfuse PostgreSQL settings."""

    pg_host: str = "langfuse-postgres"
    pg_port: int = 5433
    pg_db: str = "langfuse"
    pg_user: str = "langfuse_user"
    pg_password: str

    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        case_sensitive=False,
        env_file=".env",
    )


class RedisSettings(BaseSettings):
    """Redis settings."""

    host: str = "redis"
    port: int = 6379
    password: str
    db_cache: int = 0
    db_rate_limit: int = 1
    db_session: int = 2
    db_translation: int = 3

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
        env_file=".env",
    )

    @property
    def url_cache(self) -> str:
        """Redis URL for cache database."""
        return (
            f"redis://:{self.password}@{self.host}:{self.port}/{self.db_cache}"
        )

    @property
    def url_rate_limit(self) -> str:
        """Redis URL for rate limit database."""
        return (
            f"redis://:{self.password}@{self.host}:{self.port}/{self.db_rate_limit}"
        )

    @property
    def url_session(self) -> str:
        """Redis URL for session database."""
        return (
            f"redis://:{self.password}@{self.host}:{self.port}/{self.db_session}"
        )

    @property
    def url_translation(self) -> str:
        """Redis URL for translation cache database."""
        return (
            f"redis://:{self.password}@{self.host}:{self.port}/{self.db_translation}"
        )


class MilvusSettings(BaseSettings):
    """Milvus vector database settings."""

    host: str = "milvus"
    port: int = 19530
    collection_text: str = "ministry_text"
    collection_image: str = "ministry_images"

    model_config = SettingsConfigDict(
        env_prefix="MILVUS_",
        case_sensitive=False,
        env_file=".env",
    )


class MinIOSettings(BaseSettings):
    """MinIO object storage settings."""

    endpoint: str = "minio:9000"
    access_key: str
    secret_key: str
    bucket_documents: str = "documents"
    bucket_models: str = "models"
    bucket_backups: str = "backups"
    use_ssl: bool = False

    model_config = SettingsConfigDict(
        env_prefix="MINIO_",
        case_sensitive=False,
        env_file=".env",
    )


class JWTSettings(BaseSettings):
    """JWT authentication settings."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_prefix="JWT_",
        case_sensitive=False,
        env_file=".env",
    )


class LLMSettings(BaseSettings):
    """LLM service settings."""

    service_url: str = "http://llm-service:8002"
    model_standard: str = "meta-llama/Llama-3.1-8B-Instruct-AWQ"
    model_longctx: str = "mistralai/Mistral-NeMo-Instruct-2407-AWQ"
    model_multimodal: str = "google/gemma-3-12b-it-awq"
    gpu_memory_utilization: float = 0.85
    max_model_len_standard: int = 8192
    max_model_len_longctx: int = 131072
    max_model_len_multimodal: int = 8192

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=False,
        env_file=".env",
    )


class RAGSettings(BaseSettings):
    """RAG service settings."""

    service_url: str = "http://rag-service:8001"
    embedding_model: str = "BAAI/bge-m3"
    vision_embedding_model: str = "google/siglip-so400m-patch14-384"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 10
    rerank_top_k: int = 5
    confidence_threshold: float = 0.65
    cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        case_sensitive=False,
        env_file=".env",
    )


class SpeechSettings(BaseSettings):
    """Speech service settings."""

    service_url: str = "http://speech-service:8003"
    stt_model: str = "ai4bharat/indicconformer-hi-en"
    tts_hindi_model: str = "ai4bharat/indic-tts-hindi"
    tts_english_model: str = "coqui/tts-english"
    sample_rate: int = 16000

    model_config = SettingsConfigDict(
        env_prefix="SPEECH_",
        case_sensitive=False,
        env_file=".env",
    )


class TranslationSettings(BaseSettings):
    """Translation service settings."""

    service_url: str = "http://translation-service:8004"
    model: str = "ai4bharat/indictrans2-indic-en-1B"
    cache_ttl_seconds: int = 86400

    model_config = SettingsConfigDict(
        env_prefix="TRANSLATION_",
        case_sensitive=False,
        env_file=".env",
    )


class OCRSettings(BaseSettings):
    """OCR service settings."""

    service_url: str = "http://ocr-service:8005"
    tesseract_lang: str = "hin+eng"
    easyocr_langs: str = "hi,en"

    model_config = SettingsConfigDict(
        env_prefix="OCR_",
        case_sensitive=False,
        env_file=".env",
    )


class IngestionSettings(BaseSettings):
    """Data ingestion service settings."""

    service_url: str = "http://data-ingestion:8006"
    scrape_interval_hours: int = 24
    max_concurrent_spiders: int = 4
    respect_robots_txt: bool = True

    model_config = SettingsConfigDict(
        env_prefix="INGESTION_",
        case_sensitive=False,
        env_file=".env",
    )


class TrainingSettings(BaseSettings):
    """Model training service settings."""

    service_url: str = "http://model-training:8007"
    lora_rank: int = 16
    lora_alpha: int = 32
    learning_rate: float = 2e-4
    epochs: int = 3
    batch_size: int = 4

    model_config = SettingsConfigDict(
        env_prefix="TRAINING_",
        case_sensitive=False,
        env_file=".env",
    )


class LangfuseSettings(BaseSettings):
    """Langfuse LLM observability settings."""

    host: str = "http://langfuse:3001"
    public_key: str
    secret_key: str

    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        case_sensitive=False,
        env_file=".env",
    )


class SessionSettings(BaseSettings):
    """Session management settings."""

    idle_timeout_seconds: int = 1800
    max_turns: int = 50
    context_window_tokens: int = 4096

    model_config = SettingsConfigDict(
        env_prefix="SESSION_",
        case_sensitive=False,
        env_file=".env",
    )


class RetentionSettings(BaseSettings):
    """Data retention policy settings."""

    conversations_days: int = 90
    feedback_days: int = 365
    audit_log_days: int = 730
    analytics_days: int = 365
    translation_cache_days: int = 30

    model_config = SettingsConfigDict(
        env_prefix="RETENTION_",
        case_sensitive=False,
        env_file=".env",
    )


class RateLimitSettings(BaseSettings):
    """Rate limit settings (requests per minute)."""

    admin: int = 120
    editor: int = 90
    viewer: int = 30
    api_consumer: int = 60

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        case_sensitive=False,
        env_file=".env",
    )


class NGINXSettings(BaseSettings):
    """NGINX reverse proxy settings."""

    domain: str = "culture.gov.in"
    ssl_cert_path: str = "/etc/nginx/ssl/cert.pem"
    ssl_key_path: str = "/etc/nginx/ssl/key.pem"
    cors_allowed_origins: str = "https://culture.gov.in,https://www.culture.gov.in"

    model_config = SettingsConfigDict(
        env_prefix="NGINX_",
        case_sensitive=False,
        env_file=".env",
    )


class GPUSettings(BaseSettings):
    """GPU driver and CUDA settings."""

    driver_min_version: str = "535"
    cuda_min_version: str = "12.1"

    model_config = SettingsConfigDict(
        env_prefix="NVIDIA_",
        case_sensitive=False,
        env_file=".env",
    )


def get_settings() -> dict:
    """Get all settings as a dictionary."""
    return {
        "app": AppSettings(),
        "postgres": PostgresSettings(),
        "langfuse_postgres": LangfusePostgresSettings(),
        "redis": RedisSettings(),
        "milvus": MilvusSettings(),
        "minio": MinIOSettings(),
        "jwt": JWTSettings(),
        "llm": LLMSettings(),
        "rag": RAGSettings(),
        "speech": SpeechSettings(),
        "translation": TranslationSettings(),
        "ocr": OCRSettings(),
        "ingestion": IngestionSettings(),
        "training": TrainingSettings(),
        "langfuse": LangfuseSettings(),
        "session": SessionSettings(),
        "retention": RetentionSettings(),
        "rate_limit": RateLimitSettings(),
        "nginx": NGINXSettings(),
        "gpu": GPUSettings(),
    }
