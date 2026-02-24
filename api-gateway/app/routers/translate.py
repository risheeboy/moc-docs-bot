"""Translation endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from ..models import (
    TranslateRequest,
    TranslateResponse,
    TranslateBatchRequest,
    TranslateBatchResponse,
    DetectRequest,
    DetectResponse,
)
from ..dependencies import get_redis, verify_jwt_token, verify_api_key
from ..services.translation_client import TranslationClient
from ..services.cache_service import CacheService
from ..config import get_settings
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1", tags=["translation"])
logger = logging.getLogger(__name__)


@router.post("/translate", response_model=TranslateResponse, tags=["translation"])
async def translate(
    request_obj: TranslateRequest,
    request: Request = None,
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Translate text between Indian languages."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Initialize clients
        translation_client = TranslationClient(settings.translation_service_url)
        cache_service = CacheService(redis)

        # Check cache
        cache_key = cache_service.get_key(
            "translate", request_obj.text, request_obj.source_language, request_obj.target_language
        )
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Translation cache hit", extra={"request_id": request_id})
            return TranslateResponse(
                translated_text=cached.get("translated_text", ""),
                source_language=request_obj.source_language,
                target_language=request_obj.target_language,
                cached=True,
                request_id=request_id,
                timestamp=datetime.utcnow(),
            )

        # Translate via service
        response = await translation_client.translate(
            request_obj.text,
            request_obj.source_language,
            request_obj.target_language,
            request_id,
        )

        result = TranslateResponse(
            translated_text=response.get("translated_text", ""),
            source_language=request_obj.source_language,
            target_language=request_obj.target_language,
            cached=False,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

        # Cache result
        await cache_service.set(
            cache_key,
            {"translated_text": result.translated_text},
            settings.retention_translation_cache_days * 86400,
        )

        return result

    except Exception as e:
        logger.error(f"Translation error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )


@router.post("/translate/batch", response_model=TranslateBatchResponse, tags=["translation"])
async def translate_batch(
    request_obj: TranslateBatchRequest,
    request: Request = None,
    redis = Depends(get_redis),
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Batch translate multiple texts."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        translation_client = TranslationClient(settings.translation_service_url)

        response = await translation_client.translate_batch(
            request_obj.texts,
            request_obj.source_language,
            request_obj.target_language,
            request_id,
        )

        return TranslateBatchResponse(
            translations=response.get("translations", []),
            source_language=request_obj.source_language,
            target_language=request_obj.target_language,
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Batch translation error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )


@router.post("/translate/detect", response_model=DetectResponse, tags=["translation"])
async def detect_language(
    request_obj: DetectRequest,
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Detect language of text."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        translation_client = TranslationClient(settings.translation_service_url)

        response = await translation_client.detect(request_obj.text, request_id)

        return DetectResponse(
            language=response.get("language", "en"),
            confidence=response.get("confidence", 0.0),
            script=response.get("script"),
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Language detection error: {e}", extra={"request_id": request_id})
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )
