"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings read from environment variables."""

    # Application
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=False)
    app_log_level: str = Field(default="INFO")
    app_secret_key: str = Field(default="dev-secret-key-change-in-production")

    # PostgreSQL (main) / RDS
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="ragqa")
    postgres_user: str = Field(default="ragqa_user")
    postgres_password: str = Field(default="password")
    postgres_ssl_mode: str = Field(default="disable")

    # Redis / ElastiCache
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)
    redis_ssl: bool = Field(default=False)
    redis_db_cache: int = Field(default=0)
    redis_db_rate_limit: int = Field(default=1)
    redis_db_session: int = Field(default=2)
    redis_db_translation: int = Field(default=3)

    # Milvus
    milvus_host: str = Field(default="milvus")
    milvus_port: int = Field(default=19530)
    milvus_collection_text: str = Field(default="ministry_text")
    milvus_collection_image: str = Field(default="ministry_images")

    # AWS S3
    aws_default_region: str = Field(default="ap-south-1")
    aws_s3_bucket_documents: str = Field(default="ragqa-documents")
    aws_s3_bucket_models: str = Field(default="ragqa-models")
    aws_s3_bucket_backups: str = Field(default="ragqa-backups")

    # Authentication (disable for VPC-only access)
    auth_enabled: bool = Field(default=False)

    # JWT
    jwt_secret_key: str = Field(default="dev-jwt-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # LLM Service
    llm_service_url: str = Field(default="http://llm-service:8002")
    llm_model_standard: str = Field(default="meta-llama/Llama-3.1-8B-Instruct-AWQ")
    llm_model_longctx: str = Field(default="mistralai/Mistral-NeMo-Instruct-2407-AWQ")
    llm_model_multimodal: str = Field(default="google/gemma-3-12b-it-awq")

    # RAG Service
    rag_service_url: str = Field(default="http://rag-service:8001")
    rag_embedding_model: str = Field(default="BAAI/bge-m3")
    rag_confidence_threshold: float = Field(default=0.65)
    rag_cache_ttl_seconds: int = Field(default=3600)

    # Speech Service
    speech_service_url: str = Field(default="http://speech-service:8003")

    # Translation Service
    translation_service_url: str = Field(default="http://translation-service:8004")

    # OCR Service
    ocr_service_url: str = Field(default="http://ocr-service:8005")

    # Data Ingestion
    ingestion_service_url: str = Field(default="http://data-ingestion:8006")

    # Model Training
    training_service_url: str = Field(default="http://model-training:8007")

    # Langfuse
    langfuse_host: str = Field(default="http://langfuse:3001")
    langfuse_public_key: Optional[str] = Field(default=None)
    langfuse_secret_key: Optional[str] = Field(default=None)

    # Session
    session_idle_timeout_seconds: int = Field(default=1800)
    session_max_turns: int = Field(default=50)
    session_context_window_tokens: int = Field(default=4096)

    # Data Retention (days)
    retention_conversations_days: int = Field(default=90)
    retention_feedback_days: int = Field(default=365)
    retention_audit_log_days: int = Field(default=730)
    retention_analytics_days: int = Field(default=365)
    retention_translation_cache_days: int = Field(default=30)

    # Rate Limits (requests per minute, per role)
    rate_limit_admin: int = Field(default=120)
    rate_limit_editor: int = Field(default=90)
    rate_limit_viewer: int = Field(default=30)
    rate_limit_api_consumer: int = Field(default=60)

    # NGINX / CORS
    nginx_domain: str = Field(default="culture.gov.in")
    cors_allowed_origins: str = Field(default="https://culture.gov.in,https://www.culture.gov.in")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def postgres_url(self) -> str:
        """PostgreSQL/RDS connection URL."""
        url = f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        if self.postgres_ssl_mode != "disable":
            url += f"?sslmode={self.postgres_ssl_mode}"
        return url

    @property
    def redis_url(self) -> str:
        """Redis/ElastiCache connection URL."""
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse CORS allowed origins."""
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
