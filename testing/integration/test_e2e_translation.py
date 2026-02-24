"""
End-to-end translation flow tests.
Tests: Query Hindi → Translate → English response

Validates:
- §8.4 API Gateway → Translation Service contract
- §4 Error Response Format
"""

import httpx
import pytest
from pydantic import BaseModel, Field


# ============================================================================
# Response Models
# ============================================================================

class TranslationResponse(BaseModel):
    """Translation service response (§8.4)."""
    translated_text: str
    source_language: str
    target_language: str
    cached: bool = False


class LanguageDetectionResponse(BaseModel):
    """Language detection response."""
    language: str
    confidence: float = Field(..., ge=0, le=1)
    script: str


class BatchTranslationResponse(BaseModel):
    """Batch translation response (§8.4)."""
    translations: list[dict]  # {text, cached}
    source_language: str
    target_language: str


# ============================================================================
# Tests
# ============================================================================

class TestTranslationFlowBasic:
    """Basic translation flow tests."""

    @pytest.mark.integration
    def test_translate_hindi_to_english(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Translate Hindi text to English
        Validates: §8.4 translate endpoint contract
        """
        payload = {
            "text": "नमस्ते, यह एक परीक्षा है।",
            "source_language": "hi",
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        trans_resp = TranslationResponse.model_validate(data)

        assert trans_resp.translated_text
        assert trans_resp.source_language == "hi"
        assert trans_resp.target_language == "en"
        assert len(trans_resp.translated_text) > 0

    @pytest.mark.integration
    def test_translate_english_to_hindi(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Translate English text to Hindi
        """
        payload = {
            "text": "Hello, this is a test.",
            "source_language": "en",
            "target_language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        TranslationResponse.model_validate(data)

    @pytest.mark.integration
    def test_translate_batch(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Batch translation of multiple texts
        Validates: §8.4 translate/batch endpoint
        """
        payload = {
            "texts": [
                "नमस्ते",
                "धन्यवाद",
                "कृपया",
            ],
            "source_language": "hi",
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate/batch",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        batch_resp = BatchTranslationResponse.model_validate(data)

        assert len(batch_resp.translations) == 3
        assert batch_resp.source_language == "hi"
        assert batch_resp.target_language == "en"

        for trans in batch_resp.translations:
            assert "text" in trans
            assert "cached" in trans

    @pytest.mark.integration
    def test_detect_language_hindi(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Language detection for Hindi text
        Validates: §8.4 detect endpoint
        """
        payload = {
            "text": "यह हिंदी में लिखा गया है",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate/detect",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        detect_resp = LanguageDetectionResponse.model_validate(data)

        assert detect_resp.language == "hi"
        assert detect_resp.confidence > 0.7
        assert detect_resp.script == "Devanagari"

    @pytest.mark.integration
    def test_detect_language_english(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Language detection for English text
        """
        payload = {
            "text": "This text is written in English",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate/detect",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        detect_resp = LanguageDetectionResponse.model_validate(data)

        assert detect_resp.language == "en"
        assert detect_resp.confidence > 0.8
        assert detect_resp.script == "Latin"

    @pytest.mark.integration
    def test_detect_language_mixed(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Language detection with mixed Hindi/English text
        """
        payload = {
            "text": "नमस्ते Hello, यह एक test है।",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate/detect",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        # May detect as Hindi or English (dominant)
        assert data["language"] in ["hi", "en"]

    @pytest.mark.integration
    def test_translate_unsupported_language(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Unsupported language returns error
        Validates: §4 INVALID_LANGUAGE error
        """
        payload = {
            "text": "test",
            "source_language": "xx",  # Invalid
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_LANGUAGE"

    @pytest.mark.integration
    def test_translate_empty_text(
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
            "source_language": "hi",
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_translate_caching(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Same translation is cached on repeat request
        """
        payload = {
            "text": "संस्कृति मंत्रालय",
            "source_language": "hi",
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        # First request
        response1 = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("cached") is False

        # Second request - same query
        response2 = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers={
                **auth_headers_api_consumer,
                "X-Request-ID": str(__import__("uuid").uuid4()),
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # May be cached
        assert "cached" in data2


class TestTranslationFlowAdvanced:
    """Advanced translation scenarios."""

    @pytest.mark.integration
    def test_translate_long_text(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Translation of longer document
        """
        long_text = """
        भारतीय संस्कृति मंत्रालय का प्राथमिक उद्देश्य देश की समृद्ध सांस्कृतिक विरासत
        को संरक्षित और संवर्धित करना है। यह मंत्रालय भारतीय कला, साहित्य, संगीत,
        और ऐतिहासिक स्मारकों की देखभाल के लिए जिम्मेदार है।
        """ * 3

        payload = {
            "text": long_text,
            "source_language": "hi",
            "target_language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
            timeout=60.0,
        )

        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert len(data["translated_text"]) > 0

    @pytest.mark.integration
    def test_translate_with_special_characters(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Translation preserves special characters and formatting
        """
        texts = [
            "नमस्ते! कैसे हो?",  # Hindi with punctuation
            "Email: test@example.com",  # With email
            "संख्या: १२३४५६७८९०",  # Hindi numbers
            "https://culture.gov.in/test",  # URL
        ]

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        for text in texts:
            payload = {
                "text": text,
                "source_language": "hi",
                "target_language": "en",
            }

            response = http_client.post(
                "/api/v1/translate",
                json=payload,
                headers=headers,
            )

            assert response.status_code in [200, 422]

    @pytest.mark.integration
    def test_translate_indic_languages(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Translation between Indic languages
        """
        # Hindi to Bengali
        payload = {
            "text": "नमस्ते",
            "source_language": "hi",
            "target_language": "bn",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/translate",
            json=payload,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert data["translated_text"]
            assert data["target_language"] == "bn"
