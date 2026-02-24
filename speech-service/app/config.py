"""Configuration for Speech Service"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class SpeechConfig(BaseSettings):
    """Speech service configuration from environment variables"""

    # Service metadata
    service_name: str = "speech-service"
    version: str = "1.0.0"
    app_env: str = os.getenv("APP_ENV", "production")
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("APP_LOG_LEVEL", "INFO")

    # STT Configuration
    stt_model: str = os.getenv(
        "SPEECH_STT_MODEL", "ai4bharat/indicconformer-hi-en"
    )
    stt_device: str = "cuda"  # Use GPU for inference
    stt_max_duration_seconds: int = 300  # 5 minutes max
    stt_sample_rate: int = int(os.getenv("SPEECH_SAMPLE_RATE", "16000"))

    # TTS Configuration - Hindi
    tts_hindi_model: str = os.getenv(
        "SPEECH_TTS_HINDI_MODEL", "ai4bharat/indic-tts-hindi"
    )

    # TTS Configuration - English (Coqui fallback)
    tts_english_model: str = os.getenv(
        "SPEECH_TTS_ENGLISH_MODEL", "coqui/tts-english"
    )

    # Model cache directory
    model_cache_dir: str = os.getenv(
        "HF_HOME", "/app/models"
    )  # HuggingFace cache

    # Audio processing
    supported_audio_formats: list[str] = ["wav", "mp3", "webm", "ogg"]
    supported_output_formats: list[str] = ["wav", "mp3"]
    default_output_format: str = "mp3"

    # TTS output sample rate
    tts_sample_rate: int = 22050  # Standard for TTS models

    # Inference settings
    confidence_threshold: float = 0.5  # Minimum confidence for STT results
    voice_activity_detection: bool = True  # Enable VAD preprocessing
    device: str = "cuda"  # GPU device

    # Resource limits
    max_audio_file_size_mb: int = 50  # Maximum audio file size
    max_text_length_for_tts: int = 5000  # Maximum text length for TTS

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = SpeechConfig()
