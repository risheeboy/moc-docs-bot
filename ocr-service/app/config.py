"""Configuration for OCR Service."""

import os
from pydantic_settings import BaseSettings


class OCRSettings(BaseSettings):
    """OCR service configuration from environment variables."""

    # Service metadata
    service_name: str = "ocr-service"
    version: str = "1.0.0"
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")

    # OCR Engines
    tesseract_lang: str = os.getenv("OCR_TESSERACT_LANG", "hin+eng")
    easyocr_langs: str = os.getenv("OCR_EASYOCR_LANGS", "hi,en")

    # Engine selection
    default_engine: str = "tesseract"  # "tesseract" | "easyocr" | "auto"
    enable_fallback: bool = True
    fallback_engine: str = "easyocr"

    # Preprocessing options
    enable_preprocessing: bool = True
    deskew_enabled: bool = True
    denoise_enabled: bool = True
    binarize_enabled: bool = True

    # Image size constraints
    max_image_size_mb: int = 50
    max_pdf_pages: int = 500
    target_dpi: int = 300

    # Confidence thresholds
    min_confidence: float = 0.3
    confidence_warning_threshold: float = 0.5

    # Processing timeouts
    ocr_timeout_seconds: int = 300
    pdf_extraction_timeout_seconds: int = 120

    # Batch processing
    max_batch_size: int = 100
    batch_timeout_seconds: int = 600

    # Model cache directory
    model_cache_dir: str = "/tmp/ocr_models"

    # Language-specific settings
    hindi_ligature_fixes: bool = True
    english_confidence_boost: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> OCRSettings:
    """Get OCR settings instance."""
    return OCRSettings()


settings = get_settings()
