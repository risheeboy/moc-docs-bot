"""Pytest configuration and fixtures for speech-service tests"""

import pytest
from pathlib import Path
import io
import numpy as np
import soundfile as sf
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def sample_hindi_audio() -> bytes:
    """Create a sample Hindi audio file (WAV format)"""
    sample_rate = 16000
    duration = 2
    frequency = 440
    t = np.linspace(0, duration, sample_rate * duration)
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio, sample_rate, format="WAV")
    return wav_buffer.getvalue()


@pytest.fixture(scope="session")
def sample_english_audio() -> bytes:
    """Create a sample English audio file (WAV format)"""
    sample_rate = 16000
    duration = 2
    frequency = 880
    t = np.linspace(0, duration, sample_rate * duration)
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio, sample_rate, format="WAV")
    return wav_buffer.getvalue()


def _make_stt_mock():
    """Create a fully mocked STT model with transcribe method"""
    mock = Mock()
    mock.check_model_loaded.return_value = True
    # transcribe returns (text, language, confidence, duration_seconds)
    mock.transcribe.return_value = (
        "यह एक परीक्षा है",
        "hi",
        0.92,
        2.0,
    )
    return mock


def _make_tts_mock():
    """Create a fully mocked TTS model with synthesize method"""
    mock = Mock()
    mock.check_model_loaded.return_value = True
    # synthesize returns (audio_array, sample_rate, duration)
    mock.synthesize.return_value = (
        np.random.randn(16000).astype(np.float32),
        16000,
        1.0,
    )
    return mock


def _make_audio_processor_mock():
    """Create a fully mocked audio processor"""
    mock = Mock()
    mock.validate_audio_format.side_effect = lambda filename: (
        Path(filename).suffix.lstrip(".").lower() in ["wav", "mp3", "webm", "ogg"]
    )
    mock.convert_to_wav.return_value = (
        np.random.randn(32000).astype(np.float32).tobytes(),
        16000,
    )
    mock.normalize_audio.side_effect = lambda data: data
    mock.encode_to_format.return_value = b"\x00" * 1024
    return mock


@pytest.fixture
def client():
    """FastAPI test client with fully mocked model loading and audio processing"""
    from fastapi.testclient import TestClient

    stt_mock = _make_stt_mock()
    hindi_tts_mock = _make_tts_mock()
    english_tts_mock = _make_tts_mock()
    audio_proc_mock = _make_audio_processor_mock()

    with patch('app.services.indic_conformer_stt.get_stt_model', return_value=stt_mock), \
         patch('app.services.indic_tts.get_hindi_tts_model', return_value=hindi_tts_mock), \
         patch('app.services.coqui_tts.get_english_tts_model', return_value=english_tts_mock), \
         patch('app.routers.stt.get_stt_model', return_value=stt_mock), \
         patch('app.routers.tts.get_hindi_tts_model', return_value=hindi_tts_mock), \
         patch('app.routers.tts.get_english_tts_model', return_value=english_tts_mock), \
         patch('app.routers.stt.audio_processor', audio_proc_mock), \
         patch('app.routers.tts.audio_processor', audio_proc_mock), \
         patch('app.main.get_stt_model', return_value=stt_mock), \
         patch('app.main.get_hindi_tts_model', return_value=hindi_tts_mock), \
         patch('app.main.get_english_tts_model', return_value=english_tts_mock):

        from app.main import app
        yield TestClient(app)
