"""Batch translation endpoint for multiple texts"""

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


class BatchTranslateRequest(BaseModel):
    """Batch translation request (from §8.4 Shared Contracts)"""

    texts: list[str] = Field(
        ...,
        description="List of texts to translate",
        min_items=1,
        max_items=100,
    )
    source_language: str = Field(
        ..., description="Source language code (ISO 639-1)", min_length=2, max_length=3
    )
    target_language: str = Field(
        ..., description="Target language code (ISO 639-1)", min_length=2, max_length=3
    )


class TranslationItem(BaseModel):
    """Single translation result from batch"""

    text: str = Field(..., description="Translated text")
    cached: bool = Field(..., description="Whether this translation came from cache")


class BatchTranslateResponse(BaseModel):
    """Batch translation response (from §8.4 Shared Contracts)"""

    translations: list[TranslationItem] = Field(
        ..., description="List of translated texts with cache status"
    )
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")


class ErrorDetail(BaseModel):
    """Standard error response (from §4 Shared Contracts)"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for debugging")


class ErrorResponse(BaseModel):
    """Standard error wrapper"""

    error: ErrorDetail


@router.post("/batch", response_model=BatchTranslateResponse)
async def batch_translate_texts(
    request_payload: BatchTranslateRequest, request: Request
) -> BatchTranslateResponse:
    """
    Translate multiple texts in a single request.

    Useful for translating search results or document chunks in bulk.
    Each translation is independently cached.

    **Request body (from §8.4 Shared Contracts):**
    ```json
    {
      "texts": ["text1", "text2", "text3"],
      "source_language": "en",
      "target_language": "hi"
    }
    ```

    **Response:**
    ```json
    {
      "translations": [
        {"text": "translated1", "cached": false},
        {"text": "translated2", "cached": true},
        {"text": "translated3", "cached": false}
      ],
      "source_language": "en",
      "target_language": "hi"
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

        # Validate batch size
        if len(request_payload.texts) > settings.translation_max_batch_items:
            logger.warning(
                "Batch size exceeds limit",
                batch_size=len(request_payload.texts),
                max_items=settings.translation_max_batch_items,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=ErrorDetail(
                        code="INVALID_REQUEST",
                        message=f"Batch size exceeds limit of {settings.translation_max_batch_items}",
                        request_id=request_id,
                    )
                ).model_dump(),
            )

        translations: list[TranslationItem] = []
        texts_to_translate: list[tuple[int, str]] = []  # (index, text) pairs

        logger.info(
            "Starting batch translation",
            batch_size=len(request_payload.texts),
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
            request_id=request_id,
        )

        # Same language case
        if request_payload.source_language == request_payload.target_language:
            logger.info(
                "Source and target languages are the same",
                language=request_payload.source_language,
                request_id=request_id,
            )
            for text in request_payload.texts:
                translations.append(TranslationItem(text=text, cached=True))

            return BatchTranslateResponse(
                translations=translations,
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
            )

        # Check cache for each text
        for i, text in enumerate(request_payload.texts):
            cached_translation = await translation_cache.get(
                text=text,
                source_lang=request_payload.source_language,
                target_lang=request_payload.target_language,
            )

            if cached_translation:
                translations.append(TranslationItem(text=cached_translation, cached=True))
                translation_cache_hit_total.labels(
                    source_language=request_payload.source_language,
                    target_language=request_payload.target_language,
                ).inc()
                logger.debug(
                    "Cache hit for batch item",
                    index=i,
                    request_id=request_id,
                )
            else:
                # Mark for translation
                texts_to_translate.append((i, text))
                translations.append(None)  # Placeholder

        # Translate uncached texts in batch
        if texts_to_translate:
            logger.info(
                "Translating uncached texts",
                count=len(texts_to_translate),
                request_id=request_id,
            )

            texts_only = [text for _, text in texts_to_translate]
            translated_batch = await indictrans2_engine.translate_batch(
                texts=texts_only,
                source_language=request_payload.source_language,
                target_language=request_payload.target_language,
            )

            # Fill in translations and cache them
            for (original_index, original_text), translated_text in zip(
                texts_to_translate, translated_batch
            ):
                translations[original_index] = TranslationItem(
                    text=translated_text, cached=False
                )

                # Cache the result
                await translation_cache.set(
                    text=original_text,
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
            "Batch translation completed successfully",
            batch_size=len(request_payload.texts),
            duration_ms=duration_ms,
            request_id=request_id,
        )

        return BatchTranslateResponse(
            translations=translations,
            source_language=request_payload.source_language,
            target_language=request_payload.target_language,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Batch translation failed",
            error=str(e),
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_ERROR",
                    message="Batch translation service encountered an error",
                    request_id=request_id,
                )
            ).model_dump(),
        )
