"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
import io
import numpy as np
import soundfile as sf


@pytest.fixture(scope="session")
def sample_hindi_audio() -> bytes:
    """Create a sample Hindi audio file (WAV format)"""
    # Create a simple sine wave as placeholder audio
    sample_rate = 16000
    duration = 2  # 2 seconds
    frequency = 440  # Hz

    t = np.linspace(0, duration, sample_rate * duration)
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

    # Save to bytes
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio, sample_rate, format="WAV")
    return wav_buffer.getvalue()


@pytest.fixture(scope="session")
def sample_english_audio() -> bytes:
    """Create a sample English audio file (WAV format)"""
    # Create a simple sine wave at different frequency
    sample_rate = 16000
    duration = 2  # 2 seconds
    frequency = 880  # Hz (different from Hindi sample)

    t = np.linspace(0, duration, sample_rate * duration)
    audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

    # Save to bytes
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio, sample_rate, format="WAV")
    return wav_buffer.getvalue()


@pytest.fixture
def client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)
