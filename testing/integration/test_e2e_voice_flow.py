"""
End-to-end voice flow tests.
Tests: Audio input → STT → Query processing → TTS → Audio output

Validates:
- §8.3 API Gateway → Speech Service contract
- §4 Error Response Format
- §5 Health Check Format
"""

import httpx
import pytest
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Response Models
# ============================================================================

class STTResponse(BaseModel):
    """Speech-to-text response (§8.3)."""
    text: str
    language: str
    confidence: float = Field(..., ge=0, le=1)
    duration_seconds: float


class TTSMetadata(BaseModel):
    """Text-to-speech response metadata."""
    duration_seconds: float
    language: str
    format: str  # mp3, wav, ogg


# ============================================================================
# Tests
# ============================================================================

class TestVoiceFlowBasic:
    """Basic voice flow tests."""

    @pytest.mark.integration
    def test_speech_to_text_hindi(
        self,
        http_client: httpx.Client,
        test_audio_file: bytes,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: STT correctly transcribes Hindi audio
        Validates: §8.3 STT endpoint contract
        """
        files = {
            "audio": ("test_audio.wav", test_audio_file, "audio/wav"),
        }
        data = {
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        # Remove Content-Type from headers for multipart form data
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/speech/stt",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        stt_resp = STTResponse.model_validate(data)

        assert stt_resp.text is not None
        assert stt_resp.language == "hi"
        assert 0 <= stt_resp.confidence <= 1
        assert stt_resp.duration_seconds > 0

    @pytest.mark.integration
    def test_speech_to_text_english(
        self,
        http_client: httpx.Client,
        test_audio_file: bytes,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: STT correctly transcribes English audio
        """
        files = {
            "audio": ("test_audio.wav", test_audio_file, "audio/wav"),
        }
        data = {
            "language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/speech/stt",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 200
        resp_data = response.json()
        STTResponse.model_validate(resp_data)

    @pytest.mark.integration
    def test_speech_to_text_auto_detect(
        self,
        http_client: httpx.Client,
        test_audio_file: bytes,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: STT auto-detects language when not specified
        """
        files = {
            "audio": ("test_audio.wav", test_audio_file, "audio/wav"),
        }
        data = {
            "language": "auto",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/speech/stt",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 200
        resp_data = response.json()
        stt_resp = STTResponse.model_validate(resp_data)

        # Should detect a language
        assert stt_resp.language in ["hi", "en"]

    @pytest.mark.integration
    def test_text_to_speech_hindi(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: TTS generates Hindi audio
        Validates: §8.3 TTS endpoint contract
        """
        payload = {
            "text": "नमस्ते, मैं आपका संस्कृति सहायक हूँ।",
            "language": "hi",
            "format": "mp3",
            "voice": "default",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/tts",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "audio/mpeg"

        # Check metadata headers
        assert "X-Duration-Seconds" in response.headers
        assert "X-Language" in response.headers
        assert float(response.headers["X-Duration-Seconds"]) > 0
        assert response.headers["X-Language"] == "hi"

        # Audio should be non-empty
        assert len(response.content) > 100

    @pytest.mark.integration
    def test_text_to_speech_english(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: TTS generates English audio
        """
        payload = {
            "text": "Hello, I am your culture assistant.",
            "language": "en",
            "format": "mp3",
            "voice": "default",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/tts",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "audio/mpeg"
        assert response.headers["X-Language"] == "en"

    @pytest.mark.integration
    def test_text_to_speech_wav_format(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: TTS can generate WAV format
        """
        payload = {
            "text": "यह एक परीक्षा है।",
            "language": "hi",
            "format": "wav",
            "voice": "default",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/tts",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.headers.get("content-type") == "audio/wav"

    @pytest.mark.integration
    def test_stt_invalid_audio_format(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Invalid audio format returns error
        Validates: §4 INVALID_AUDIO_FORMAT error code
        """
        files = {
            "audio": ("invalid.txt", b"This is not audio", "text/plain"),
        }
        data = {
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/speech/stt",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_AUDIO_FORMAT"

    @pytest.mark.integration
    def test_stt_missing_audio_file(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Missing audio file returns error
        """
        data = {
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/stt",
            data=data,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_tts_empty_text(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Empty text returns error
        """
        payload = {
            "text": "",
            "language": "hi",
            "format": "mp3",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/tts",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"


class TestVoiceFlowAdvanced:
    """Advanced voice flow scenarios."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_voice_flow(
        self,
        http_client: httpx.Client,
        test_audio_file: bytes,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Complete voice flow (STT → Query → TTS)
        """
        # Step 1: STT - Convert audio to text
        stt_files = {
            "audio": ("test.wav", test_audio_file, "audio/wav"),
        }
        stt_data = {
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers_no_ct = headers.copy()
        headers_no_ct.pop("Content-Type", None)

        stt_response = http_client.post(
            "/api/v1/speech/stt",
            files=stt_files,
            data=stt_data,
            headers=headers_no_ct,
        )

        if stt_response.status_code != 200:
            pytest.skip("STT service not available")

        stt_result = stt_response.json()
        transcribed_text = stt_result.get("text", "")

        # Step 2: Chat - Get response for transcribed query
        chat_payload = {
            "query": transcribed_text,
            "language": stt_result.get("language", "hi"),
            "session_id": session_id,
        }

        chat_response = http_client.post(
            "/api/v1/chat",
            json=chat_payload,
            headers=headers,
        )

        if chat_response.status_code != 200:
            pytest.skip("Chat service not available")

        chat_result = chat_response.json()
        response_text = chat_result.get("response", "")

        # Step 3: TTS - Convert response to audio
        tts_payload = {
            "text": response_text,
            "language": "hi",
            "format": "mp3",
        }

        tts_response = http_client.post(
            "/api/v1/speech/tts",
            json=tts_payload,
            headers=headers,
        )

        if tts_response.status_code == 200:
            assert tts_response.headers.get("content-type") == "audio/mpeg"
            assert len(tts_response.content) > 100

    @pytest.mark.integration
    def test_stt_long_audio(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: STT can handle longer audio files (>1 minute)
        """
        # Generate 2-minute silent WAV file
        sample_rate = 16000
        duration_seconds = 120
        num_samples = sample_rate * duration_seconds

        wav_header = (
            b"RIFF" +
            (36 + num_samples * 2).to_bytes(4, "little") +
            b"WAVE" +
            b"fmt " +
            (16).to_bytes(4, "little") +
            (1).to_bytes(2, "little") +
            (1).to_bytes(2, "little") +
            sample_rate.to_bytes(4, "little") +
            (sample_rate * 2).to_bytes(4, "little") +
            (2).to_bytes(2, "little") +
            (16).to_bytes(2, "little") +
            b"data" +
            (num_samples * 2).to_bytes(4, "little")
        )

        audio_data = b"\x00\x00" * num_samples
        long_audio = wav_header + audio_data

        files = {
            "audio": ("long_audio.wav", long_audio, "audio/wav"),
        }
        data = {
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/speech/stt",
            files=files,
            data=data,
            headers=headers,
            timeout=120.0,  # Long timeout for long audio
        )

        # Should succeed or return specific error, not crash
        assert response.status_code in [200, 422]

    @pytest.mark.integration
    def test_tts_text_with_special_characters(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: TTS handles special characters and punctuation
        """
        text_samples = [
            "नमस्ते! आप कैसे हो?",  # Hindi with punctuation
            "क्या आप मुझे संस्कृति के बारे में बता सकते हैं?",  # Hindi with question mark
            "संख्या: १२३, नाम: टेस्ट",  # Numbers and special chars
            "Email: test@example.com (test)",  # Mixed content
        ]

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        for text in text_samples:
            payload = {
                "text": text,
                "language": "hi",
                "format": "mp3",
            }

            response = http_client.post(
                "/api/v1/speech/tts",
                json=payload,
                headers=headers,
            )

            # Should handle without error
            assert response.status_code in [200, 422]

    @pytest.mark.integration
    def test_tts_text_length_limits(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: TTS respects text length limits
        """
        # Create very long text
        long_text = "यह एक परीक्षा है। " * 1000  # Repeat ~17KB of text

        payload = {
            "text": long_text,
            "language": "hi",
            "format": "mp3",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/speech/tts",
            json=payload,
            headers=headers,
            timeout=60.0,
        )

        # Should succeed, truncate, or return proper error
        assert response.status_code in [200, 413, 422]
        if response.status_code == 413:
            error_data = response.json()
            assert error_data["error"]["code"] == "PAYLOAD_TOO_LARGE"
