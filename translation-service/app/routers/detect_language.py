"""Language detection endpoint"""

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.services.language_detector import language_detector
from app.config import settings

logger = structlog.get_logger()

router = APIRouter(tags=["detection"])


class DetectLanguageRequest(BaseModel):
    """Language detection request (from §8.4 Shared Contracts)"""

    text: str = Field(
        ..., description="Text to detect language for", min_length=1, max_length=5000
    )


class DetectLanguageResponse(BaseModel):
    """Language detection response (from §8.4 Shared Contracts)"""

    language: str = Field(
        ..., description="Detected language code (ISO 639-1)"
    )
    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    script: str = Field(
        ..., description="Writing system (e.g., Devanagari, Latin, Bengali)"
    )


class ErrorDetail(BaseModel):
    """Standard error response (from §4 Shared Contracts)"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")


class ErrorResponse(BaseModel):
    """Standard error wrapper"""

    error: ErrorDetail


@router.post("/detect", response_model=DetectLanguageResponse)
async def detect_language(
    request_payload: DetectLanguageRequest, request: Request
) -> DetectLanguageResponse:
    """
    Auto-detect the language of input text.

    Uses AI4Bharat language identification model to detect the language.

    **Request body (from §8.4 Shared Contracts):**
    ```json
    {
      "text": "यह हिंदी में लिखा गया है"
    }
    ```

    **Response:**
    ```json
    {
      "language": "hi",
      "confidence": 0.97,
      "script": "Devanagari"
    }
    ```
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    try:
        logger.info(
            "Starting language detection",
            text_length=len(request_payload.text),
            request_id=request_id,
        )

        # Detect language
        detected_language, confidence = await language_detector.detect(
            text=request_payload.text
        )

        # Validate detected language is in supported set
        if detected_language not in settings.supported_languages:
            logger.warning(
                "Detected unsupported language",
                language=detected_language,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_LANGUAGE",
                        message=f"Detected language '{detected_language}' is not supported",
                        request_id=request_id,
                    )
                ).model_dump(),
            )

        # Get script for language
        script = settings.language_scripts.get(detected_language, "Unknown")

        logger.info(
            "Language detection completed successfully",
            language=detected_language,
            confidence=confidence,
            script=script,
            request_id=request_id,
        )

        return DetectLanguageResponse(
            language=detected_language,
            confidence=confidence,
            script=script,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Language detection failed",
            error=str(e),
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Language detection service encountered an error",
                    request_id=request_id,
                )
            ).model_dump(),
        )
