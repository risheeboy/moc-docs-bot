"""Coqui TTS for English text-to-speech fallback"""

import logging
import time
import numpy as np
import torch
from typing import Tuple

logger = logging.getLogger(__name__)


class CoquiTTS:
    """Coqui TTS for English voice synthesis"""

    SUPPORTED_LANGUAGES = ["en"]
    DEFAULT_VOICE = "default"

    def __init__(self):
        """Initialize Coqui TTS model"""
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 22050  # Standard for TTS

        # Load model
        self._load_model()

    def _load_model(self):
        """Load Coqui TTS model"""
        try:
            start_time = time.time()
            logger.info("Loading Coqui TTS model for English")

            # Import TTS from coqui-ai/TTS
            try:
                from TTS.api import TTS

                # Load model
                self.model = TTS(
                    model_name="tts_models/en/ljspeech/glow-tts",
                    gpu=self.device == "cuda",
                )
                self.sample_rate = 22050

            except ImportError:
                logger.warning(
                    "Coqui TTS not installed, will use placeholder synthesis"
                )
                self.model = None

            load_time = time.time() - start_time
            logger.info(f"Coqui TTS model loaded in {load_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load Coqui TTS model: {e}")
            logger.info("Will use placeholder synthesis")

    def synthesize(
        self, text: str, language: str = "en", voice: str = "default"
    ) -> Tuple[np.ndarray, int, float]:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            language: Language code (only "en" supported)
            voice: Voice name ("default" for standard)

        Returns:
            (audio_array, sample_rate, duration_seconds)
        """
        start_time = time.time()

        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Coqui TTS only supports: {self.SUPPORTED_LANGUAGES}")

        try:
            # Pre-process text
            text = self._preprocess_text(text, language)

            # Validate text length
            max_length = 5000
            if len(text) > max_length:
                logger.warning(f"Text truncated from {len(text)} to {max_length}")
                text = text[:max_length]

            # Generate audio
            if self.model:
                try:
                    # Use actual Coqui TTS model
                    logger.info(f"Synthesizing English text ({len(text)} chars)")

                    # Save to temporary file
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name

                    # Synthesize
                    self.model.tts_to_file(text=text, file_path=tmp_path)

                    # Load audio file
                    import soundfile as sf
                    audio_array, sr = sf.read(tmp_path, dtype=np.float32)

                    # Cleanup
                    import os
                    os.unlink(tmp_path)

                    duration = len(audio_array) / sr

                except Exception as e:
                    logger.warning(f"Coqui TTS synthesis failed: {e}, using placeholder")
                    # Fallback to placeholder
                    duration_estimate = len(text) / 100.0
                    audio_length = int(self.sample_rate * duration_estimate)
                    audio_array = np.zeros(audio_length, dtype=np.float32)
                    duration = audio_length / self.sample_rate
            else:
                # No model loaded, use placeholder
                duration_estimate = len(text) / 100.0
                audio_length = int(self.sample_rate * duration_estimate)
                audio_array = np.zeros(audio_length, dtype=np.float32)
                duration = audio_length / self.sample_rate
                logger.info(f"Using placeholder synthesis for {len(text)} chars")

            # Record metrics
            inference_time = time.time() - start_time
            logger.info(
                f"TTS completed: {language}, duration: {duration:.2f}s, "
                f"inference: {inference_time:.2f}s"
            )

            return audio_array, self.sample_rate, duration

        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise

    def _preprocess_text(self, text: str, language: str) -> str:
        """Pre-process text for synthesis"""
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove special characters that might break synthesis
        text = text.replace("\n", " ").replace("\r", " ")

        return text

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages"""
        return self.SUPPORTED_LANGUAGES

    def check_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None


# Global instance
tts_english_model = None


def get_english_tts_model() -> CoquiTTS:
    """Get or initialize English TTS model (singleton pattern)"""
    global tts_english_model
    if tts_english_model is None:
        tts_english_model = CoquiTTS()
    return tts_english_model
