"""Text-to-Speech router"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import uuid
import numpy as np
import io

from app.config import config
from app.services.indic_tts import get_hindi_tts_model
from app.services.coqui_tts import get_english_tts_model
from app.services.audio_processor import audio_processor
from app.utils.metrics import (
    record_tts_request,
    record_tts_duration,
    record_tts_output_duration,
    record_processing_error,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """TTS request format (from shared contracts §8.3)"""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    language: str = Field(
        default="hi", description="Language code: hi or en"
    )
    format: str = Field(
        default="mp3", description="Output format: wav or mp3"
    )
    voice: str = Field(
        default="default", description="Voice name (currently only 'default' supported)"
    )


class ErrorDetail(BaseModel):
    """Error response format"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description")
    details: Optional[dict] = Field(default=None, description="Additional details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: ErrorDetail


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using AI4Bharat IndicTTS (Hindi) or Coqui TTS (English)

    Request format:
        {
            "text": "Text to synthesize",
            "language": "hi" or "en",
            "format": "wav" or "mp3",
            "voice": "default"
        }

    Returns:
        Binary audio data with headers:
        - Content-Type: audio/mpeg or audio/wav
        - X-Duration-Seconds: duration of generated audio
        - X-Language: language of synthesis

    Error Codes:
        - INVALID_REQUEST: Malformed request
        - INVALID_LANGUAGE: Unsupported language code
        - INVALID_REQUEST: Invalid audio format
        - MODEL_LOADING: Model still loading
        - PROCESSING_FAILED: TTS processing error
        - INTERNAL_ERROR: Unexpected server error
    """
    request_id = str(uuid.uuid4())

    try:
        # Validate language
        if request.language not in ["hi", "en"]:
            logger.warning(f"Invalid language for TTS: {request.language}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_LANGUAGE",
                        "message": f"Language '{request.language}' not supported for TTS. Use 'hi' or 'en'",
                        "request_id": request_id,
                    }
                },
            )

        # Validate format
        if request.format not in config.supported_output_formats:
            logger.warning(f"Invalid output format: {request.format}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": f"Unsupported output format: {request.format}. Supported: {config.supported_output_formats}",
                        "request_id": request_id,
                    }
                },
            )

        # Validate text
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Text cannot be empty",
                        "request_id": request_id,
                    }
                },
            )

        if len(request.text) > config.max_text_length_for_tts:
            logger.warning(
                f"Text too long: {len(request.text)} > {config.max_text_length_for_tts}"
            )
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": f"Text exceeds {config.max_text_length_for_tts} character limit",
                        "request_id": request_id,
                    }
                },
            )

        logger.info(
            f"Processing TTS request: language={request.language}, format={request.format}, "
            f"text_len={len(request.text)}"
        )

        # Get appropriate TTS model
        if request.language == "hi":
            tts_model = get_hindi_tts_model()
            model_name = "indic-tts"
        else:  # en
            tts_model = get_english_tts_model()
            model_name = "coqui-tts"

        if not tts_model.check_model_loaded():
            logger.warning(f"TTS model not loaded: {model_name}")
            record_tts_request(request.language, request.format, "error")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "MODEL_LOADING",
                        "message": "TTS model is still loading. Please try again.",
                        "request_id": request_id,
                    }
                },
            )

        # Synthesize speech
        import time
        start_time = time.time()

        audio_array, sample_rate, duration = tts_model.synthesize(
            text=request.text,
            language=request.language,
            voice=request.voice,
        )

        if audio_array is None or len(audio_array) == 0:
            logger.error("TTS returned empty audio")
            record_tts_request(request.language, request.format, "error")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "PROCESSING_FAILED",
                        "message": "Failed to generate audio from text",
                        "request_id": request_id,
                    }
                },
            )

        # Record metrics
        inference_time = time.time() - start_time
        record_tts_duration(inference_time, request.language, model_name)
        record_tts_output_duration(duration, request.language)
        record_tts_request(request.language, request.format, "success")

        # Encode audio to requested format
        if request.format == "mp3":
            audio_bytes = audio_processor.encode_to_format(
                audio_array, sample_rate, "mp3", bitrate="192k"
            )
            media_type = "audio/mpeg"
        else:  # wav
            audio_bytes = audio_processor.encode_to_format(
                audio_array, sample_rate, "wav"
            )
            media_type = "audio/wav"

        logger.info(
            f"TTS success: {request.language}, duration={duration:.2f}s, "
            f"output_size={len(audio_bytes) / 1024:.2f}KB"
        )

        # Return audio with headers
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type=media_type,
            headers={
                "X-Duration-Seconds": str(duration),
                "X-Language": request.language,
                "Cache-Control": "no-cache",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        record_tts_request(request.language, request.format, "error")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(e),
                    "request_id": request_id,
                }
            },
        )
    except Exception as e:
        logger.error(f"TTS processing error: {e}", exc_info=True)
        record_tts_request(request.language, request.format, "error")
        record_processing_error("tts", "processing_error")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Text-to-speech processing failed",
                    "details": {"error": str(e)},
                    "request_id": request_id,
                }
            },
        )
