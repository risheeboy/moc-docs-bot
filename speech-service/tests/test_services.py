"""Tests for Speech Service internal services"""

import pytest
from pathlib import Path
import numpy as np
import soundfile as sf
import io


class TestAudioProcessor:
    """Tests for AudioProcessor service"""

    def test_validate_audio_format_wav(self):
        """Test WAV format validation"""
        from app.services.audio_processor import audio_processor

        assert audio_processor.validate_audio_format("test.wav") is True

    def test_validate_audio_format_mp3(self):
        """Test MP3 format validation"""
        from app.services.audio_processor import audio_processor

        assert audio_processor.validate_audio_format("test.mp3") is True

    def test_validate_audio_format_webm(self):
        """Test WebM format validation"""
        from app.services.audio_processor import audio_processor

        assert audio_processor.validate_audio_format("test.webm") is True

    def test_validate_audio_format_ogg(self):
        """Test OGG format validation"""
        from app.services.audio_processor import audio_processor

        assert audio_processor.validate_audio_format("test.ogg") is True

    def test_validate_audio_format_invalid(self):
        """Test invalid format validation"""
        from app.services.audio_processor import audio_processor

        assert audio_processor.validate_audio_format("test.txt") is False
        assert audio_processor.validate_audio_format("test.jpg") is False

    def test_get_audio_duration(self, sample_hindi_audio: bytes):
        """Test audio duration extraction"""
        from app.services.audio_processor import audio_processor

        duration = audio_processor.get_audio_duration(sample_hindi_audio, "wav")

        assert duration > 0
        assert isinstance(duration, float)

    def test_normalize_audio(self, sample_hindi_audio: bytes):
        """Test audio normalization"""
        from app.services.audio_processor import audio_processor

        normalized = audio_processor.normalize_audio(sample_hindi_audio)

        assert len(normalized) > 0
        assert isinstance(normalized, bytes)


class TestLanguageDetector:
    """Tests for LanguageDetector service"""

    def test_language_detector_initialization(self):
        """Test language detector can be initialized"""
        from app.services.language_detect import LanguageDetector

        detector = LanguageDetector()
        assert detector is not None
        assert len(detector.SUPPORTED_LANGUAGES) > 0

    def test_language_detector_supported_languages(self):
        """Test supported languages are defined"""
        from app.services.language_detect import LanguageDetector

        detector = LanguageDetector()
        assert "hi" in detector.SUPPORTED_LANGUAGES
        assert "en" in detector.SUPPORTED_LANGUAGES

    def test_language_detection_returns_tuple(self, sample_hindi_audio: bytes):
        """Test language detection returns (language, confidence) tuple"""
        from app.services.language_detect import language_detector

        language, confidence = language_detector.detect(sample_hindi_audio)

        assert isinstance(language, str)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_language_detection_returns_supported_language(self, sample_hindi_audio: bytes):
        """Test language detection returns a supported language"""
        from app.services.language_detect import language_detector

        language, confidence = language_detector.detect(sample_hindi_audio)

        assert language in ["hi", "en"]


class TestSTTModel:
    """Tests for IndicConformer STT Model"""

    def test_stt_model_initialization(self):
        """Test STT model can be initialized"""
        from app.services.indic_conformer_stt import IndicConformerSTT

        try:
            model = IndicConformerSTT()
            assert model is not None
        except Exception as e:
            # Model loading may fail if GPU not available or models not downloaded
            pytest.skip(f"Model loading failed: {e}")

    def test_stt_model_supported_languages(self):
        """Test STT model supported languages"""
        from app.services.indic_conformer_stt import IndicConformerSTT

        assert IndicConformerSTT.SUPPORTED_LANGUAGES == ["hi", "en"]

    def test_stt_model_singleton(self):
        """Test STT model uses singleton pattern"""
        from app.services.indic_conformer_stt import get_stt_model

        model1 = get_stt_model()
        model2 = get_stt_model()

        assert model1 is model2


class TestTTSModels:
    """Tests for TTS Models"""

    def test_hindi_tts_model_initialization(self):
        """Test Hindi TTS model can be initialized"""
        from app.services.indic_tts import IndicTTS

        try:
            model = IndicTTS()
            assert model is not None
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")

    def test_hindi_tts_supported_languages(self):
        """Test Hindi TTS supported languages"""
        from app.services.indic_tts import IndicTTS

        assert IndicTTS.SUPPORTED_LANGUAGES == ["hi"]

    def test_english_tts_model_initialization(self):
        """Test English TTS model (Coqui) can be initialized"""
        from app.services.coqui_tts import CoquiTTS

        try:
            model = CoquiTTS()
            assert model is not None
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")

    def test_english_tts_supported_languages(self):
        """Test English TTS supported languages"""
        from app.services.coqui_tts import CoquiTTS

        assert CoquiTTS.SUPPORTED_LANGUAGES == ["en"]

    def test_hindi_tts_model_singleton(self):
        """Test Hindi TTS model uses singleton pattern"""
        from app.services.indic_tts import get_hindi_tts_model

        model1 = get_hindi_tts_model()
        model2 = get_hindi_tts_model()

        assert model1 is model2

    def test_english_tts_model_singleton(self):
        """Test English TTS model uses singleton pattern"""
        from app.services.coqui_tts import get_english_tts_model

        model1 = get_english_tts_model()
        model2 = get_english_tts_model()

        assert model1 is model2
