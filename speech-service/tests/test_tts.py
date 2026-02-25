"""Tests for Text-to-Speech functionality"""

import pytest
from fastapi.testclient import TestClient
import json


def get_error(data: dict) -> dict:
    """Extract error from response data, handling FastAPI detail wrapping"""
    if "detail" in data and isinstance(data["detail"], dict) and "error" in data["detail"]:
        return data["detail"]["error"]
    if "error" in data:
        return data["error"]
    return data


class TestTTSEndpoint:
    """Tests for POST /tts endpoint"""

    def test_tts_with_hindi_text(self, client: TestClient):
        """Test TTS with Hindi text"""
        response = client.post(
            "/tts",
            json={"text": "नमस्ते, यह एक परीक्षा है", "language": "hi", "format": "mp3", "voice": "default"},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("Content-Type") in ["audio/mpeg", "audio/wav"]
            assert "X-Duration-Seconds" in response.headers
            assert "X-Language" in response.headers
            assert response.headers["X-Language"] == "hi"
            assert len(response.content) > 0

    def test_tts_with_english_text(self, client: TestClient):
        """Test TTS with English text"""
        response = client.post(
            "/tts",
            json={"text": "Hello, this is a test", "language": "en", "format": "mp3", "voice": "default"},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("Content-Type") in ["audio/mpeg", "audio/wav"]
            assert response.headers["X-Language"] == "en"

    def test_tts_with_wav_output_format(self, client: TestClient):
        """Test TTS with WAV output format"""
        response = client.post(
            "/tts",
            json={"text": "नमस्ते", "language": "hi", "format": "wav", "voice": "default"},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert "audio" in response.headers.get("Content-Type", "")
            assert "X-Duration-Seconds" in response.headers

    def test_tts_with_mp3_output_format(self, client: TestClient):
        """Test TTS with MP3 output format"""
        response = client.post(
            "/tts",
            json={"text": "Hello", "language": "en", "format": "mp3", "voice": "default"},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert "audio" in response.headers.get("Content-Type", "")

    def test_tts_with_invalid_language(self, client: TestClient):
        """Test TTS with unsupported language code"""
        response = client.post(
            "/tts",
            json={"text": "Some text", "language": "invalid", "format": "mp3", "voice": "default"},
        )

        assert response.status_code == 400
        error = get_error(response.json())
        assert error["code"] == "INVALID_LANGUAGE"

    def test_tts_with_invalid_format(self, client: TestClient):
        """Test TTS with unsupported output format"""
        response = client.post(
            "/tts",
            json={"text": "Some text", "language": "hi", "format": "invalid_format", "voice": "default"},
        )

        assert response.status_code == 400
        error = get_error(response.json())
        assert error["code"] == "INVALID_REQUEST"

    def test_tts_with_empty_text(self, client: TestClient):
        """Test TTS with empty text — Pydantic enforces min_length=1"""
        response = client.post(
            "/tts",
            json={"text": "", "language": "hi", "format": "mp3", "voice": "default"},
        )

        # Pydantic validation rejects empty text (min_length=1) with 422
        assert response.status_code in [400, 422]

    def test_tts_with_very_long_text(self, client: TestClient):
        """Test TTS with text exceeding length limit"""
        long_text = "a" * 6000

        response = client.post(
            "/tts",
            json={"text": long_text, "language": "hi", "format": "mp3", "voice": "default"},
        )

        # Pydantic validation rejects >5000 chars (max_length=5000) with 422
        assert response.status_code in [413, 422]

    def test_tts_response_headers_format(self, client: TestClient):
        """Test TTS response headers match specification §8.3"""
        response = client.post(
            "/tts",
            json={"text": "नमस्ते", "language": "hi", "format": "mp3", "voice": "default"},
        )

        if response.status_code == 200:
            assert "X-Duration-Seconds" in response.headers
            assert "X-Language" in response.headers
            duration = float(response.headers["X-Duration-Seconds"])
            assert duration > 0
            assert response.headers["X-Language"] in ["hi", "en"]

    def test_tts_request_id_header(self, client: TestClient):
        """Test that request ID is returned in response headers"""
        response = client.post(
            "/tts",
            json={"text": "नमस्ते", "language": "hi", "format": "mp3", "voice": "default"},
        )

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_tts_error_response_format(self, client: TestClient):
        """Test error response format matches specification §4"""
        response = client.post(
            "/tts",
            json={"text": "Text", "language": "invalid", "format": "mp3", "voice": "default"},
        )

        assert response.status_code == 400
        error = get_error(response.json())
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)

    def test_tts_missing_required_field(self, client: TestClient):
        """Test TTS with missing required field"""
        response = client.post(
            "/tts",
            json={"language": "hi", "format": "mp3"},
        )

        assert response.status_code == 422


class TestTTSLanguageSupport:
    """Tests for TTS language support"""

    def test_tts_hindi_language_supported(self, client: TestClient):
        """Test that Hindi language is supported"""
        response = client.post(
            "/tts",
            json={"text": "नमस्ते", "language": "hi", "format": "mp3", "voice": "default"},
        )

        assert response.status_code in [200, 503]

    def test_tts_english_language_supported(self, client: TestClient):
        """Test that English language is supported"""
        response = client.post(
            "/tts",
            json={"text": "Hello", "language": "en", "format": "mp3", "voice": "default"},
        )

        assert response.status_code in [200, 503]


class TestTTSMetrics:
    """Tests for TTS metrics recording"""

    def test_tts_metrics_endpoint_exists(self, client: TestClient):
        """Test that /metrics endpoint exists and is accessible"""
        response = client.get("/metrics")
        assert response.status_code == 200
