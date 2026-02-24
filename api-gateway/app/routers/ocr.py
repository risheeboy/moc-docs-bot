"""OCR endpoints for image/document text extraction."""

from fastapi import APIRouter, Depends, HTTPException, Request, File, UploadFile, Form
from ..dependencies import verify_jwt_token, verify_api_key
from ..services.ocr_client import OCRClient
from ..config import get_settings
from datetime import datetime
import uuid
import logging

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])
logger = logging.getLogger(__name__)


@router.post("/upload", tags=["ocr"])
async def ocr_upload(
    file: UploadFile = File(...),
    languages: str = Form(default="hi,en"),
    engine: str = Form(default="auto"),
    request: Request = None,
    settings = Depends(get_settings),
    _: any = Depends(verify_jwt_token) or Depends(verify_api_key),
):
    """Extract text from image/PDF using OCR."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    try:
        # Read file
        file_bytes = await file.read()

        # Call OCR service
        ocr_client = OCRClient(settings.ocr_service_url)
        response = await ocr_client.ocr(
            file_bytes=file_bytes,
            filename=file.filename,
            languages=languages,
            engine=engine,
            request_id=request_id,
        )

        return {
            "text": response.get("text", ""),
            "pages": response.get("pages", []),
            "language": response.get("language", "en"),
            "engine_used": response.get("engine_used", "auto"),
            "confidence": response.get("confidence", 0.0),
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(f"OCR upload error: {e}", extra={"request_id": request_id})
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
