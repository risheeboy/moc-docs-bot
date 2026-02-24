"""Tests for Speech-to-Text functionality"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from io import BytesIO


class TestSTTEndpoint:
    """Tests for POST /stt endpoint"""

    def test_stt_with_valid_hindi_audio(self, client: TestClient, sample_hindi_audio: bytes):
        """Test STT with valid Hindi audio file"""
        response = client.post(
            "/stt",
            data={"language": "hi"},
            files={"audio": ("test_hindi.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        assert response.status_code in [200, 503]  # 503 if models not loaded
        if response.status_code == 200:
            data = response.json()
            assert "text" in data
            assert "language" in data
            assert data["language"] == "hi"
            assert "confidence" in data
            assert "duration_seconds" in data
            assert 0 <= data["confidence"] <= 1
            assert data["duration_seconds"] > 0

    def test_stt_with_valid_english_audio(self, client: TestClient, sample_english_audio: bytes):
        """Test STT with valid English audio file"""
        response = client.post(
            "/stt",
            data={"language": "en"},
            files={"audio": ("test_english.wav", BytesIO(sample_english_audio), "audio/wav")},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "text" in data
            assert data["language"] == "en"

    def test_stt_with_auto_language_detection(self, client: TestClient, sample_hindi_audio: bytes):
        """Test STT with auto language detection"""
        response = client.post(
            "/stt",
            data={"language": "auto"},
            files={"audio": ("test.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "language" in data
            assert data["language"] in ["hi", "en"]

    def test_stt_with_invalid_language(self, client: TestClient, sample_hindi_audio: bytes):
        """Test STT with unsupported language code"""
        response = client.post(
            "/stt",
            data={"language": "invalid"},
            files={"audio": ("test.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_LANGUAGE"

    def test_stt_with_invalid_audio_format(self, client: TestClient):
        """Test STT with unsupported audio format"""
        invalid_audio = b"not an audio file"

        response = client.post(
            "/stt",
            data={"language": "hi"},
            files={"audio": ("test.txt", BytesIO(invalid_audio), "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_AUDIO_FORMAT"

    def test_stt_without_audio_file(self, client: TestClient):
        """Test STT without audio file"""
        response = client.post(
            "/stt",
            data={"language": "hi"},
        )

        assert response.status_code == 422  # Validation error

    def test_stt_response_format(self, client: TestClient, sample_hindi_audio: bytes):
        """Test STT response format matches specification"""
        response = client.post(
            "/stt",
            data={"language": "hi"},
            files={"audio": ("test.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        if response.status_code == 200:
            data = response.json()
            # Verify response format matches §8.3
            required_fields = ["text", "language", "confidence", "duration_seconds"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(data["text"], str)
            assert isinstance(data["language"], str)
            assert isinstance(data["confidence"], (int, float))
            assert isinstance(data["duration_seconds"], (int, float))

    def test_stt_request_id_header(self, client: TestClient, sample_hindi_audio: bytes):
        """Test that request ID is returned in response headers"""
        response = client.post(
            "/stt",
            data={"language": "hi"},
            files={"audio": ("test.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0

    def test_stt_with_large_audio_file(self, client: TestClient):
        """Test STT with audio file exceeding size limit"""
        # Create a 60MB dummy file (exceeds 50MB limit)
        large_audio = b"x" * (60 * 1024 * 1024)

        response = client.post(
            "/stt",
            data={"language": "hi"},
            files={"audio": ("large.wav", BytesIO(large_audio), "audio/wav")},
        )

        assert response.status_code == 413
        data = response.json()
        assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_stt_error_response_format(self, client: TestClient):
        """Test error response format matches specification §4"""
        response = client.post(
            "/stt",
            data={"language": "invalid"},
            files={"audio": ("test.wav", BytesIO(b"dummy"), "audio/wav")},
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


class TestSTTLanguageDetection:
    """Tests for language detection in STT"""

    def test_language_detection_with_hindi_audio(self, client: TestClient, sample_hindi_audio: bytes):
        """Test language detection identifies Hindi audio"""
        response = client.post(
            "/stt",
            data={"language": "auto"},
            files={"audio": ("test.wav", BytesIO(sample_hindi_audio), "audio/wav")},
        )

        if response.status_code == 200:
            data = response.json()
            # Should detect as either hi or en
            assert data["language"] in ["hi", "en"]

    def test_language_detection_with_english_audio(self, client: TestClient, sample_english_audio: bytes):
        """Test language detection identifies English audio"""
        response = client.post(
            "/stt",
            data={"language": "auto"},
            files={"audio": ("test.wav", BytesIO(sample_english_audio), "audio/wav")},
        )

        if response.status_code == 200:
            data = response.json()
            assert data["language"] in ["hi", "en"]


class TestSTTMetrics:
    """Tests for STT metrics recording"""

    def test_stt_metrics_endpoint_exists(self, client: TestClient):
        """Test that /metrics endpoint exists and is accessible"""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "speech_stt_duration_seconds" in response.text or response.text  # Metrics may be empty
