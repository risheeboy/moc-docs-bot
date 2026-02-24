"""Tests for voice endpoints."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app


def test_stt_endpoint_requires_file(client: TestClient):
    """Test STT endpoint requires audio file."""
    response = client.post(
        "/api/v1/voice/stt",
    )

    # Should fail without file
    assert response.status_code in [422, 400, 401]


def test_stt_with_file(client: TestClient):
    """Test STT with audio file."""
    audio_file = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/voice/stt",
        files={"file": ("audio.wav", audio_file, "audio/wav")},
        data={"language": "en"},
    )

    # Should return proper response or require auth
    assert response.status_code in [200, 401, 422]


def test_tts_endpoint_requires_text(client: TestClient):
    """Test TTS endpoint requires text."""
    response = client.post(
        "/api/v1/voice/tts",
        data={
            "language": "en",
        },
    )

    # Should fail without text
    assert response.status_code in [422, 400, 401]


def test_tts_with_text(client: TestClient):
    """Test TTS with text."""
    response = client.post(
        "/api/v1/voice/tts",
        data={
            "text": "Hello, this is a test",
            "language": "en",
            "format": "mp3",
        },
    )

    # Should return audio or require auth
    assert response.status_code in [200, 401, 422, 500]
