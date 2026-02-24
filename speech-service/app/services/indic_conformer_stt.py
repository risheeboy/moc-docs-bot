"""AI4Bharat IndicConformer Speech-to-Text service"""

import logging
import tempfile
import time
from pathlib import Path
from typing import Tuple
import torch
import librosa
import numpy as np
from transformers import AutoModelForCTC, AutoProcessor, pipeline

from app.config import config
from app.utils.metrics import (
    record_stt_duration,
    record_stt_request,
    record_stt_audio_duration,
    record_processing_error,
)
from app.services.language_detect import language_detector

logger = logging.getLogger(__name__)


class IndicConformerSTT:
    """AI4Bharat IndicConformer for Hindi and English STT"""

    # Supported languages for IndicConformer
    SUPPORTED_LANGUAGES = ["hi", "en"]

    def __init__(self):
        """Initialize IndicConformer model"""
        self.model = None
        self.processor = None
        self.device = config.device
        self.sample_rate = config.stt_sample_rate
        self.model_name = config.stt_model

        # Load model
        self._load_model()

    def _load_model(self):
        """Load IndicConformer model from HuggingFace"""
        try:
            start_time = time.time()
            logger.info(f"Loading IndicConformer model: {self.model_name}")

            # Check for GPU availability
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                self.device = "cpu"

            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                cache_dir=config.model_cache_dir,
            )

            # Load model
            self.model = AutoModelForCTC.from_pretrained(
                self.model_name,
                cache_dir=config.model_cache_dir,
            ).to(self.device)

            # Set to evaluation mode
            self.model.eval()

            load_time = time.time() - start_time
            logger.info(f"IndicConformer model loaded in {load_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load IndicConformer model: {e}")
            raise

    def transcribe(
        self, audio_data: bytes, language: str = "auto"
    ) -> Tuple[str, str, float, float]:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio bytes
            language: Language code ("hi", "en", or "auto")

        Returns:
            (text, language, confidence, duration_seconds)
        """
        start_time = time.time()

        try:
            # Load audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Load audio with librosa
            y, sr = librosa.load(tmp_path, sr=self.sample_rate)
            duration = librosa.get_duration(y=y, sr=sr)

            # Auto-detect language if needed
            if language == "auto":
                detected_lang, lang_confidence = language_detector.detect(
                    audio_data, self.sample_rate
                )
                language = detected_lang
                logger.info(f"Auto-detected language: {language}")
            else:
                lang_confidence = 0.95  # High confidence for explicit language

            # Validate language
            if language not in self.SUPPORTED_LANGUAGES:
                logger.error(f"Unsupported language: {language}")
                record_stt_request(language, "error")
                raise ValueError(f"Language {language} not supported")

            # Prepare input features
            inputs = self.processor(
                y,
                sampling_rate=self.sample_rate,
                return_tensors="pt",
                padding="longest",
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Get predictions
            predicted_ids = torch.argmax(logits, dim=-1)

            # Decode transcription
            text = self.processor.batch_decode(predicted_ids)[0]

            # Post-process text
            text = self._postprocess_text(text, language)

            # Calculate confidence (placeholder - real models provide this)
            confidence = 0.85  # Placeholder

            # Record metrics
            inference_time = time.time() - start_time
            record_stt_duration(inference_time, language)
            record_stt_audio_duration(duration, language)
            record_stt_request(language, "success")

            logger.info(
                f"STT completed: {language}, duration: {duration:.2f}s, "
                f"inference: {inference_time:.2f}s"
            )

            # Cleanup
            Path(tmp_path).unlink()

            return text, language, confidence, duration

        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            record_stt_request(language, "error")
            record_processing_error("stt", "transcription_failed")
            raise

    def _postprocess_text(self, text: str, language: str) -> str:
        """Post-process transcribed text"""
        # Remove extra spaces
        text = " ".join(text.split())

        # Language-specific post-processing
        if language == "hi":
            # Remove any stray English characters in Hindi text
            pass

        return text

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages"""
        return self.SUPPORTED_LANGUAGES

    def check_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.processor is not None


# Global instance
stt_model = None


def get_stt_model() -> IndicConformerSTT:
    """Get or initialize STT model (singleton pattern)"""
    global stt_model
    if stt_model is None:
        stt_model = IndicConformerSTT()
    return stt_model
