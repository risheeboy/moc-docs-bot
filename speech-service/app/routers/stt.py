"""Speech-to-Text router"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
import uuid
from pathlib import Path

from app.config import config
from app.services.indic_conformer_stt import get_stt_model
from app.services.audio_processor import audio_processor
from app.utils.metrics import record_stt_request, record_processing_error

logger = logging.getLogger(__name__)
router = APIRouter()


class STTResponse(BaseModel):
    """STT response format (from shared contracts §8.3)"""

    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected/specified language code")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for transcription"
    )
    duration_seconds: float = Field(
        ..., description="Duration of input audio in seconds"
    )


class ErrorDetail(BaseModel):
    """Error response format (from shared contracts §4)"""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description")
    details: Optional[dict] = Field(default=None, description="Additional details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: ErrorDetail


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(
        ..., description="Audio file (WAV, MP3, WebM, or OGG format)"
    ),
    language: Optional[str] = Form(
        default="auto", description="Language code: hi, en, or auto for auto-detection"
    ),
):
    """
    Convert speech to text using AI4Bharat IndicConformer

    Args:
        audio: Audio file upload (multipart/form-data)
        language: Language code ("hi", "en", or "auto" for auto-detection)

    Returns:
        STTResponse with transcribed text, language, confidence, and duration

    Error Codes:
        - INVALID_AUDIO_FORMAT: Unsupported audio format
        - PAYLOAD_TOO_LARGE: Audio file exceeds size limit
        - INVALID_LANGUAGE: Unsupported language code
        - PROCESSING_FAILED: STT processing error
        - INTERNAL_ERROR: Unexpected server error
    """
    request_id = str(uuid.uuid4())

    try:
        # Validate language
        if language not in ["auto", "hi", "en"]:
            logger.warning(f"Invalid language requested: {language}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_LANGUAGE",
                        "message": f"Language '{language}' not supported. Use 'hi', 'en', or 'auto'",
                        "request_id": request_id,
                    }
                },
            )

        # Validate file format
        if not audio.filename:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": "Audio file is required",
                        "request_id": request_id,
                    }
                },
            )

        file_ext = Path(audio.filename).suffix.lstrip(".").lower()
        if not audio_processor.validate_audio_format(audio.filename):
            logger.warning(f"Invalid audio format: {file_ext}")
            record_processing_error("stt", "invalid_format")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_AUDIO_FORMAT",
                        "message": f"Unsupported audio format: {file_ext}. Supported: wav, mp3, webm, ogg",
                        "request_id": request_id,
                    }
                },
            )

        # Read audio file
        audio_data = await audio.read()

        # Check file size
        file_size_mb = len(audio_data) / (1024 * 1024)
        if file_size_mb > config.max_audio_file_size_mb:
            logger.warning(
                f"Audio file too large: {file_size_mb:.2f}MB > {config.max_audio_file_size_mb}MB"
            )
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": f"Audio file exceeds {config.max_audio_file_size_mb}MB limit",
                        "request_id": request_id,
                    }
                },
            )

        # Convert audio to WAV if needed
        if file_ext != "wav":
            logger.info(f"Converting {file_ext} to WAV")
            audio_data, sample_rate = audio_processor.convert_to_wav(
                audio_data, file_ext, config.stt_sample_rate
            )
        else:
            sample_rate = config.stt_sample_rate

        # Normalize audio
        audio_data = audio_processor.normalize_audio(audio_data)

        # Get STT model
        stt_model = get_stt_model()

        if not stt_model.check_model_loaded():
            logger.error("STT model not loaded")
            record_stt_request(language, "error")
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "code": "MODEL_LOADING",
                        "message": "STT model is still loading. Please try again.",
                        "request_id": request_id,
                    }
                },
            )

        # Run STT
        logger.info(f"Processing STT request: language={language}, size={file_size_mb:.2f}MB")

        text, detected_language, confidence, duration = stt_model.transcribe(
            audio_data, language=language
        )

        if not text or text.strip() == "":
            logger.warning("Empty transcription result")
            record_stt_request(detected_language, "empty")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "PROCESSING_FAILED",
                        "message": "No speech detected in audio",
                        "request_id": request_id,
                    }
                },
            )

        # Check confidence threshold
        if confidence < config.confidence_threshold:
            logger.warning(
                f"Low confidence transcription: {confidence:.2f} < {config.confidence_threshold}"
            )

        # Record success
        record_stt_request(detected_language, "success")

        logger.info(
            f"STT success: {detected_language}, confidence={confidence:.2f}, "
            f"duration={duration:.2f}s, text_len={len(text)}"
        )

        return STTResponse(
            text=text,
            language=detected_language,
            confidence=confidence,
            duration_seconds=duration,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        record_stt_request(language, "error")
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
        logger.error(f"STT processing error: {e}", exc_info=True)
        record_stt_request(language, "error")
        record_processing_error("stt", "processing_error")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Speech-to-text processing failed",
                    "details": {"error": str(e)},
                    "request_id": request_id,
                }
            },
        )
