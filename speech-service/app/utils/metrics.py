"""Prometheus metrics for Speech Service"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Optional

# STT Metrics
speech_stt_duration_seconds = Histogram(
    "speech_stt_duration_seconds",
    "Duration of STT inference in seconds",
    labelnames=["language", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

speech_stt_requests_total = Counter(
    "speech_stt_requests_total",
    "Total number of STT requests",
    labelnames=["language", "status"],
)

speech_stt_audio_duration_seconds = Histogram(
    "speech_stt_audio_duration_seconds",
    "Duration of input audio in seconds",
    labelnames=["language"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# TTS Metrics
speech_tts_duration_seconds = Histogram(
    "speech_tts_duration_seconds",
    "Duration of TTS inference in seconds",
    labelnames=["language", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

speech_tts_requests_total = Counter(
    "speech_tts_requests_total",
    "Total number of TTS requests",
    labelnames=["language", "format", "status"],
)

speech_tts_output_duration_seconds = Histogram(
    "speech_tts_output_duration_seconds",
    "Duration of generated audio in seconds",
    labelnames=["language"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# Model loading metrics
speech_models_loaded = Gauge(
    "speech_models_loaded",
    "Number of speech models currently loaded in memory",
)

speech_model_load_duration_seconds = Histogram(
    "speech_model_load_duration_seconds",
    "Time taken to load a speech model",
    labelnames=["model_type", "model_name"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0),
)

# GPU metrics
speech_gpu_memory_usage_bytes = Gauge(
    "speech_gpu_memory_usage_bytes",
    "GPU memory usage in bytes for speech models",
)

speech_gpu_available = Gauge(
    "speech_gpu_available",
    "Whether GPU is available (1=yes, 0=no)",
)

# Error metrics
speech_processing_errors_total = Counter(
    "speech_processing_errors_total",
    "Total number of speech processing errors",
    labelnames=["operation", "error_type"],
)


def record_stt_duration(duration_seconds: float, language: str, model: str = "indicconformer"):
    """Record STT processing duration"""
    speech_stt_duration_seconds.labels(language=language, model=model).observe(
        duration_seconds
    )


def record_stt_request(language: str, status: str):
    """Record STT request"""
    speech_stt_requests_total.labels(language=language, status=status).inc()


def record_stt_audio_duration(duration_seconds: float, language: str):
    """Record input audio duration"""
    speech_stt_audio_duration_seconds.labels(language=language).observe(
        duration_seconds
    )


def record_tts_duration(duration_seconds: float, language: str, model: str = "indic-tts"):
    """Record TTS processing duration"""
    speech_tts_duration_seconds.labels(language=language, model=model).observe(
        duration_seconds
    )


def record_tts_request(language: str, format: str, status: str):
    """Record TTS request"""
    speech_tts_requests_total.labels(language=language, format=format, status=status).inc()


def record_tts_output_duration(duration_seconds: float, language: str):
    """Record generated audio duration"""
    speech_tts_output_duration_seconds.labels(language=language).observe(
        duration_seconds
    )


def set_models_loaded(count: int):
    """Set number of loaded models"""
    speech_models_loaded.set(count)


def record_model_load_duration(duration_seconds: float, model_type: str, model_name: str):
    """Record model loading duration"""
    speech_model_load_duration_seconds.labels(
        model_type=model_type, model_name=model_name
    ).observe(duration_seconds)


def set_gpu_memory_usage(bytes_used: int):
    """Set GPU memory usage"""
    speech_gpu_memory_usage_bytes.set(bytes_used)


def set_gpu_available(available: bool):
    """Set GPU availability"""
    speech_gpu_available.set(1 if available else 0)


def record_processing_error(operation: str, error_type: str):
    """Record processing error"""
    speech_processing_errors_total.labels(operation=operation, error_type=error_type).inc()
