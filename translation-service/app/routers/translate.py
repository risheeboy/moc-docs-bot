"""Single text translation endpoint"""

import time
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.cache import translation_cache
from app.services.indictrans2_engine import indictrans2_engine
from app.utils.metrics import (
    translation_duration_seconds,
    translation_cache_hit_total,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/translate", tags=["translation"])


class TranslateRequest(BaseModel):
    """Single text translation request (from §8.4 Shared Contracts)"""

    text: str = Field(..., description="Text to translate", min_length=1, max_length=5000)
    source_language: str = Field(
        ..., description="Source language code (ISO 639-1)", min_length=2, max_length=3
    )
    target_language: str = Field(
        ..., description="Target language code (ISO 639-1)", min_length=2, max_length=3
    )


class TranslateResponse(BaseModel):
    """Single text translation response (from §8.4 Shared Contracts)"""

    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    cached: bool = Field(..., description="Whether this translation came from cache")


class ErrorDetail(BaseModel):
    """Standard error response (from §4 Shared Contracts)"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")


class ErrorResponse(BaseModel):
    """Standard error wrapper"""

    error: ErrorDetail


@router.post("/", response_model=TranslateResponse)
async def translate_text(
    request_payload: TranslateRequest, request: Request
) -> TranslateResponse:
    """
    Translate text from source language to target language.

    Uses IndicTrans2 model with Redis-backed caching to avoid redundant translations.

    **Request body (from §8.4 Shared Contracts):**
    ```json
    {
      "text": "Ministry of Culture promotes Indian heritage",
      "source_language": "en",
      "target_language": "hi"
    }
    ```

    **Response:**
    ```json
    {
      "translated_text": "संस्कृति मंत्रालय भारतीय विरासत को बढ़ावा देता है",
      "source_language": "en",
      "target_language": "hi",
      "cached": true
    }
    ```
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()

    try:
        # Validate language codes
        if request_payload.source_language not in settings.supported_languages:
            logger.warning(
                "Unsupported source language",
                language=request_payload.source_language,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_LANGUAGE",
                        message=f"Source language '{request_payload.source_language}' is not supported",
                        request_id=request_id,
                    )
                ).model_dump(),
            )

        if request_payload.target_language not in settings.supported_languages:
            logger.warning(
                "Unsupported target language",
                language=request_payload.target_language,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_LANGUAGE",
                        message=f"Target language '{request_payload.target_language}' is not supported",
                        request_id=request_id,
                    )
                ).model_dump(),
            )

        # Same language, return as-is
        if request_payload.source_language == request_payload.target_language:
            logger.info(
                "Source and target languages are the same",
                language=request_payload.source_language,
                request_id=request_id,
            )
            return TranslateResponse(
                translated_text=request_payload.text,
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
                cached=True,
            )

        # Check cache
        cached_translation = await translation_cache.get(
            text=request_payload.text,
            source_lang=request_payload.source_language,
            target_lang=request_payload.target_language,
        )

        if cached_translation:
            logger.info(
                "Translation cache hit",
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
                request_id=request_id,
            )
            translation_cache_hit_total.labels(
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
            ).inc()
            duration_ms = (time.time() - start_time) * 1000
            translation_duration_seconds.labels(
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
            ).observe(duration_ms / 1000)
            return TranslateResponse(
                translated_text=cached_translation,
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
                cached=True,
            )

        # Perform translation
        logger.info(
            "Starting translation",
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
            text_length=len(request_payload.text),
            request_id=request_id,
        )

        translated_text = await indictrans2_engine.translate(
            text=request_payload.text,
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
        )

        # Cache the result
        await translation_cache.set(
            text=request_payload.text,
            source_lang=request_payload.source_language,
            target_lang=request_payload.target_language,
            translation=translated_text,
            ttl_seconds=settings.translation_cache_ttl_seconds,
        )

        duration_ms = (time.time() - start_time) * 1000
        translation_duration_seconds.labels(
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
        ).observe(duration_ms / 1000)

        logger.info(
            "Translation completed successfully",
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
            duration_ms=duration_ms,
            request_id=request_id,
        )

        return TranslateResponse(
            translated_text=translated_text,
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
            cached=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Translation failed",
            error=str(e),
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Translation service encountered an error",
                    request_id=request_id,
                )
            ).model_dump(),
        )
