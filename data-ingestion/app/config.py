"""Configuration management for Data Ingestion Service."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Environment variables and configuration."""

    # Application
    app_env: str = "production"
    app_debug: bool = False
    app_log_level: str = "INFO"
    app_secret_key: str = "change-me-in-production"

    # Service registration
    service_name: str = "data-ingestion"
    service_port: int = 8006
    service_version: str = "1.0.0"

    # Ingestion configuration
    ingestion_service_url: str = "http://data-ingestion:8006"
    ingestion_scrape_interval_hours: int = 24
    ingestion_max_concurrent_spiders: int = 4
    ingestion_respect_robots_txt: bool = True
    ingestion_request_timeout_seconds: int = 30
    ingestion_max_retries: int = 3
    ingestion_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # MinIO configuration
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_documents: str = "documents"
    minio_use_ssl: bool = False

    # PostgreSQL configuration
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "ragqa"
    postgres_user: str = "ragqa_user"
    postgres_password: str = "changeme"

    # RAG Service configuration
    rag_service_url: str = "http://rag-service:8001"
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64

    # Redis configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db_cache: int = 0

    # Scraper settings
    scraper_max_pages_per_site: int = 1000
    scraper_depth_limit: int = 3
    scraper_concurrent_requests: int = 16
    scraper_download_delay: float = 1.0

    # Playwright settings
    playwright_headless: bool = True
    playwright_timeout_ms: int = 30000
    playwright_wait_for_load_state: str = "networkidle"

    # PDF settings
    pdf_min_file_size_kb: int = 1
    pdf_max_file_size_mb: int = 50
    pdf_timeout_seconds: int = 60

    # Language detection
    language_min_confidence: float = 0.7

    # Deduplication
    dedup_min_hash_num_perm: int = 128
    dedup_similarity_threshold: float = 0.95

    # Rate limiting
    rate_limit_jobs_per_minute: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
