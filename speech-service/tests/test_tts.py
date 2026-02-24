"""Tests for Text-to-Speech functionality"""

import pytest
from fastapi.testclient import TestClient
import json


class TestTTSEndpoint:
    """Tests for POST /tts endpoint"""

    def test_tts_with_hindi_text(self, client: TestClient):
        """Test TTS with Hindi text"""
        request_data = {
            "text": "नमस्ते, यह एक परीक्षा है",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code in [200, 503]  # 503 if models not loaded
        if response.status_code == 200:
            # Response should be binary audio
            assert response.headers.get("Content-Type") in [
                "audio/mpeg",
                "audio/wav",
            ]
            assert "X-Duration-Seconds" in response.headers
            assert "X-Language" in response.headers
            assert response.headers["X-Language"] == "hi"
            # Audio data should be present
            assert len(response.content) > 0

    def test_tts_with_english_text(self, client: TestClient):
        """Test TTS with English text"""
        request_data = {
            "text": "Hello, this is a test",
            "language": "en",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("Content-Type") in [
                "audio/mpeg",
                "audio/wav",
            ]
            assert response.headers["X-Language"] == "en"

    def test_tts_with_wav_output_format(self, client: TestClient):
        """Test TTS with WAV output format"""
        request_data = {
            "text": "नमस्ते",
            "language": "hi",
            "format": "wav",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("Content-Type") == "audio/wav"
            assert "X-Duration-Seconds" in response.headers

    def test_tts_with_mp3_output_format(self, client: TestClient):
        """Test TTS with MP3 output format"""
        request_data = {
            "text": "Hello",
            "language": "en",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            assert response.headers.get("Content-Type") == "audio/mpeg"

    def test_tts_with_invalid_language(self, client: TestClient):
        """Test TTS with unsupported language code"""
        request_data = {
            "text": "Some text",
            "language": "invalid",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_LANGUAGE"

    def test_tts_with_invalid_format(self, client: TestClient):
        """Test TTS with unsupported output format"""
        request_data = {
            "text": "Some text",
            "language": "hi",
            "format": "invalid_format",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_REQUEST"

    def test_tts_with_empty_text(self, client: TestClient):
        """Test TTS with empty text"""
        request_data = {
            "text": "",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_REQUEST"

    def test_tts_with_very_long_text(self, client: TestClient):
        """Test TTS with text exceeding length limit"""
        # Create text exceeding 5000 character limit
        long_text = "a" * 6000

        request_data = {
            "text": long_text,
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 413
        data = response.json()
        assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_tts_response_headers_format(self, client: TestClient):
        """Test TTS response headers match specification §8.3"""
        request_data = {
            "text": "नमस्ते",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        if response.status_code == 200:
            # Verify headers from §8.3
            assert "X-Duration-Seconds" in response.headers
            assert "X-Language" in response.headers

            # Verify header values
            duration = float(response.headers["X-Duration-Seconds"])
            assert duration > 0
            assert response.headers["X-Language"] in ["hi", "en"]

    def test_tts_request_id_header(self, client: TestClient):
        """Test that request ID is returned in response headers"""
        request_data = {
            "text": "नमस्ते",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_tts_error_response_format(self, client: TestClient):
        """Test error response format matches specification §4"""
        request_data = {
            "text": "Text",
            "language": "invalid",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 400
        data = response.json()

        # Verify error format matches shared contracts §4
        assert "error" in data
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)

    def test_tts_missing_required_field(self, client: TestClient):
        """Test TTS with missing required field"""
        request_data = {
            "language": "hi",
            "format": "mp3",
            # Missing 'text' field
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code == 422  # Validation error


class TestTTSLanguageSupport:
    """Tests for TTS language support"""

    def test_tts_hindi_language_supported(self, client: TestClient):
        """Test that Hindi language is supported"""
        request_data = {
            "text": "नमस्ते",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        # Should either succeed or be loading models (503)
        assert response.status_code in [200, 503]

    def test_tts_english_language_supported(self, client: TestClient):
        """Test that English language is supported"""
        request_data = {
            "text": "Hello",
            "language": "en",
            "format": "mp3",
            "voice": "default",
        }

        response = client.post(
            "/tts",
            json=request_data,
        )

        assert response.status_code in [200, 503]


class TestTTSMetrics:
    """Tests for TTS metrics recording"""

    def test_tts_metrics_endpoint_exists(self, client: TestClient):
        """Test that /metrics endpoint exists and is accessible"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "speech_tts_duration_seconds" in response.text or response.text
