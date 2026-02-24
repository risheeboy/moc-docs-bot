"""Configuration for Translation Service"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Translation Service Configuration"""

    # Application
    app_env: str = os.getenv("APP_ENV", "production")
    app_debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    app_log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")
    app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret-key")

    # Translation Service
    translation_model: str = os.getenv(
        "TRANSLATION_MODEL", "ai4bharat/indictrans2-indic-en-1B"
    )
    translation_cache_ttl_seconds: int = int(
        os.getenv("TRANSLATION_CACHE_TTL_SECONDS", "86400")
    )
    translation_batch_size: int = int(os.getenv("TRANSLATION_BATCH_SIZE", "32"))
    translation_max_batch_items: int = int(
        os.getenv("TRANSLATION_MAX_BATCH_ITEMS", "100")
    )
    translation_timeout_seconds: int = int(
        os.getenv("TRANSLATION_TIMEOUT_SECONDS", "60")
    )

    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db_translation: int = int(os.getenv("REDIS_DB_TRANSLATION", "3"))

    # Model paths (on disk)
    model_cache_dir: str = os.getenv(
        "MODEL_CACHE_DIR", "/root/.cache/huggingface/hub"
    )

    # Supported language codes (ISO 639-1)
    supported_languages: list[str] = [
        "hi",
        "en",
        "bn",
        "te",
        "mr",
        "ta",
        "ur",
        "gu",
        "kn",
        "ml",
        "or",
        "pa",
        "as",
        "mai",
        "sa",
        "ne",
        "sd",
        "kok",
        "doi",
        "mni",
        "sat",
        "bo",
        "ks",
    ]

    # Language script mapping (for transliteration)
    language_scripts: dict[str, str] = {
        "hi": "Devanagari",
        "en": "Latin",
        "bn": "Bengali",
        "te": "Telugu",
        "mr": "Devanagari",
        "ta": "Tamil",
        "ur": "Perso-Arabic",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "pa": "Gurmukhi",
        "as": "Bengali",
        "mai": "Devanagari",
        "sa": "Devanagari",
        "ne": "Devanagari",
        "sd": "Perso-Arabic",
        "kok": "Devanagari",
        "doi": "Devanagari",
        "mni": "Meitei",
        "sat": "Ol Chiki",
        "bo": "Devanagari",
        "ks": "Perso-Arabic",
    }

    # IndicTrans2 model supports these language pairs
    # Format: pairs of (source, target) that model can handle
    supported_language_pairs: set[tuple[str, str]] = {
        # Hindi to/from all others
        ("hi", "en"),
        ("en", "hi"),
        # English to all Indian languages
        ("en", "bn"),
        ("en", "te"),
        ("en", "mr"),
        ("en", "ta"),
        ("en", "ur"),
        ("en", "gu"),
        ("en", "kn"),
        ("en", "ml"),
        ("en", "or"),
        ("en", "pa"),
        ("en", "as"),
        ("en", "mai"),
        ("en", "ne"),
        # Indic-to-Indic (via English bridge when necessary)
        ("bn", "en"),
        ("te", "en"),
        ("mr", "en"),
        ("ta", "en"),
        ("ur", "en"),
        ("gu", "en"),
        ("kn", "en"),
        ("ml", "en"),
        ("or", "en"),
        ("pa", "en"),
        ("as", "en"),
        ("mai", "en"),
        ("ne", "en"),
    }

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
