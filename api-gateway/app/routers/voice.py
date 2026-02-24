"""Voice (STT/TTS) endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from ..models import STTResponse, TTSResponse
from ..dependencies import get_redis, verify_jwt_token, verify_api_key
from ..services.speech_client import SpeechClient
from ..config import get_settings
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])
logger = logging.getLogger(__name__)


@router.post("/stt", response_model=STTResponse, tags=["voice"])
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = Form(default="auto"),
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Convert speech (audio) to text."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Read audio file
        audio_bytes = await file.read()

        # Call speech service
        speech_client = SpeechClient(settings.speech_service_url)
        response = await speech_client.stt(audio_bytes, language, request_id)

        return STTResponse(
            text=response.get("text", ""),
            language=response.get("language", language),
            confidence=response.get("confidence", 0.0),
            duration_seconds=response.get("duration_seconds", 0.0),
            request_id=request_id,
            timestamp=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"STT error: {e}", extra={"request_id": request_id})
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


@router.post("/tts", tags=["voice"])
async def text_to_speech(
    text: str = Form(...),
    language: str = Form(default="en"),
    format: str = Form(default="mp3"),
    voice: str = Form(default="default"),
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Convert text to speech (audio)."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Call speech service
        speech_client = SpeechClient(settings.speech_service_url)
        audio_bytes = await speech_client.tts(text, language, format, voice, request_id)

        return audio_bytes

    except Exception as e:
        logger.error(f"TTS error: {e}", extra={"request_id": request_id})
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
