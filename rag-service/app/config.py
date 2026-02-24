import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """RAG Service configuration from environment variables."""

    # Application
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    app_log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")
    app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret-key-change-in-prod")

    # Milvus
    milvus_host: str = os.getenv("MILVUS_HOST", "milvus")
    milvus_port: int = int(os.getenv("MILVUS_PORT", "19530"))
    milvus_collection_text: str = os.getenv("MILVUS_COLLECTION_TEXT", "ministry_text")
    milvus_collection_image: str = os.getenv("MILVUS_COLLECTION_IMAGE", "ministry_images")

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db_cache: int = int(os.getenv("REDIS_DB_CACHE", "0"))

    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket_documents: str = os.getenv("MINIO_BUCKET_DOCUMENTS", "documents")
    minio_use_ssl: bool = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

    # RAG Configuration
    rag_embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-m3")
    rag_vision_embedding_model: str = os.getenv("RAG_VISION_EMBEDDING_MODEL", "google/siglip-so400m-patch14-384")
    rag_chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    rag_chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "10"))
    rag_rerank_top_k: int = int(os.getenv("RAG_RERANK_TOP_K", "5"))
    rag_confidence_threshold: float = float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.65"))
    rag_cache_ttl_seconds: int = int(os.getenv("RAG_CACHE_TTL_SECONDS", "3600"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
