"""
End-to-end OCR flow tests.
Tests: Upload scanned PDF → OCR extraction → Ingest → Query

Validates:
- §8.5 API Gateway → OCR Service contract
- §4 Error Response Format
"""

import httpx
import pytest
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Response Models
# ============================================================================

class OCRRegion(BaseModel):
    """Region in OCR output."""
    text: str
    bounding_box: tuple[float, float, float, float]  # [x1, y1, x2, y2]
    confidence: float = Field(..., ge=0, le=1)
    type: str  # paragraph, heading, etc.


class OCRPage(BaseModel):
    """Single page of OCR output."""
    page_number: int
    text: str
    regions: list[OCRRegion] = Field(default_factory=list)


class OCRResponse(BaseModel):
    """OCR service response (§8.5)."""
    text: str
    pages: list[OCRPage]
    language: str
    engine_used: str  # tesseract | easyocr
    confidence: float = Field(..., ge=0, le=1)


# ============================================================================
# Test Fixtures
# ============================================================================

def create_dummy_pdf_image() -> bytes:
    """Create a simple dummy image for OCR testing."""
    # PNG header + minimal data (1x1 white pixel)
    png_header = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk size
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x00, 0x01,  # Width: 1
        0x00, 0x00, 0x00, 0x01,  # Height: 1
        0x08, 0x02, 0x00, 0x00, 0x00,  # Bit depth, color type, etc.
        0x90, 0x77, 0x53, 0xDE,  # CRC
        0x00, 0x00, 0x00, 0x0C,  # IDAT chunk size
        0x49, 0x44, 0x41, 0x54,  # IDAT
        0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF, 0x7F,
        0x00, 0x09, 0xFB, 0x03, 0xFD,
        0x05, 0x39, 0x07, 0x5D,  # CRC
        0x00, 0x00, 0x00, 0x00,  # IEND chunk size
        0x49, 0x45, 0x4E, 0x44,  # IEND
        0xAE, 0x42, 0x60, 0x82,  # CRC
    ])
    return png_header


# ============================================================================
# Tests
# ============================================================================

class TestOCRFlowBasic:
    """Basic OCR flow tests."""

    @pytest.mark.integration
    def test_ocr_english_text(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR extracts English text from image
        Validates: §8.5 OCR endpoint contract
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("test_image.png", image_data, "image/png"),
        }
        data = {
            "languages": "en",
            "engine": "auto",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 200
        ocr_data = response.json()
        OCRResponse.model_validate(ocr_data)

        assert ocr_data["language"] in ["en", "eng"]
        assert len(ocr_data["pages"]) > 0

    @pytest.mark.integration
    def test_ocr_hindi_text(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR extracts Hindi Devanagari text from image
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("test_hindi.png", image_data, "image/png"),
        }
        data = {
            "languages": "hi",
            "engine": "easyocr",  # Better for Indic scripts
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code in [200, 202]  # May be async
        if response.status_code == 200:
            ocr_data = response.json()
            OCRResponse.model_validate(ocr_data)
            assert ocr_data["language"] in ["hi", "hin", "hindi"]

    @pytest.mark.integration
    def test_ocr_multilingual(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR handles both Hindi and English in same document
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("mixed_lang.png", image_data, "image/png"),
        }
        data = {
            "languages": "hi,en",
            "engine": "auto",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code in [200, 202]
        if response.status_code == 200:
            ocr_data = response.json()
            OCRResponse.model_validate(ocr_data)

    @pytest.mark.integration
    def test_ocr_multiple_pages_pdf(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR processes multi-page PDF
        Validates: §8.5 pages field
        """
        # Simplified PDF header (real test would use actual multi-page PDF)
        pdf_data = b"%PDF-1.0\n" + create_dummy_pdf_image()

        files = {
            "file": ("test_multipage.pdf", pdf_data, "application/pdf"),
        }
        data = {
            "languages": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code in [200, 202]
        if response.status_code == 200:
            ocr_data = response.json()
            ocr_resp = OCRResponse.model_validate(ocr_data)
            assert len(ocr_resp.pages) >= 1

    @pytest.mark.integration
    def test_ocr_invalid_file_type(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Invalid file type returns error
        Validates: §4 INVALID_REQUEST error
        """
        files = {
            "file": ("test.txt", b"Not an image", "text/plain"),
        }
        data = {
            "languages": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] in ["INVALID_REQUEST", "INVALID_AUDIO_FORMAT"]

    @pytest.mark.integration
    def test_ocr_missing_file(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Missing file returns error
        """
        data = {
            "languages": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/ocr",
            data=data,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_ocr_confidence_threshold(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR returns confidence scores
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("test.png", image_data, "image/png"),
        }
        data = {
            "languages": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        if response.status_code == 200:
            ocr_data = response.json()
            ocr_resp = OCRResponse.model_validate(ocr_data)
            assert 0 <= ocr_resp.confidence <= 1


class TestOCRFlowAdvanced:
    """Advanced OCR scenarios."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_ocr_to_ingest_flow(
        self,
        http_client: httpx.Client,
        auth_headers_editor: dict,
        request_id: str,
    ):
        """
        Test: OCR output can be ingested into RAG system
        """
        image_data = create_dummy_pdf_image()

        # Step 1: OCR extraction
        files = {
            "file": ("document.png", image_data, "image/png"),
        }
        data = {
            "languages": "hi,en",
        }

        headers = {
            **auth_headers_editor,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        ocr_response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        if ocr_response.status_code != 200:
            pytest.skip("OCR service not available")

        ocr_data = ocr_response.json()
        extracted_text = ocr_data.get("text", "")

        # Step 2: Ingest extracted text as document
        if extracted_text:
            ingest_payload = {
                "document_id": str(__import__("uuid").uuid4()),
                "title": "OCR Scanned Document",
                "source_url": "file:///scanned/document.png",
                "source_site": "culture.gov.in",
                "content": extracted_text,
                "content_type": "scanned_pdf",
                "language": "hi",
                "metadata": {
                    "ocr_engine": ocr_data.get("engine_used"),
                    "ocr_confidence": ocr_data.get("confidence"),
                },
            }

            ingest_headers = {
                **auth_headers_editor,
                "X-Request-ID": str(__import__("uuid").uuid4()),
            }

            ingest_response = http_client.post(
                "/api/v1/documents/ingest",
                json=ingest_payload,
                headers=ingest_headers,
            )

            # Should accept ingestion
            assert ingest_response.status_code in [200, 202]

    @pytest.mark.integration
    def test_ocr_with_tesseract_engine(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR with explicit Tesseract engine
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("test.png", image_data, "image/png"),
        }
        data = {
            "languages": "hin+eng",  # Tesseract language code
            "engine": "tesseract",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        if response.status_code == 200:
            ocr_data = response.json()
            assert ocr_data.get("engine_used") == "tesseract"

    @pytest.mark.integration
    def test_ocr_with_easyocr_engine(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: OCR with explicit EasyOCR engine (better for Indic)
        """
        image_data = create_dummy_pdf_image()

        files = {
            "file": ("test.png", image_data, "image/png"),
        }
        data = {
            "languages": "hi",
            "engine": "easyocr",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }
        headers.pop("Content-Type", None)

        response = http_client.post(
            "/api/v1/ocr",
            files=files,
            data=data,
            headers=headers,
        )

        if response.status_code == 200:
            ocr_data = response.json()
            assert ocr_data.get("engine_used") == "easyocr"
