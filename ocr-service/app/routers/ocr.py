"""OCR router for single file processing."""

from typing import Optional
import structlog
from fastapi import APIRouter, File, Form, Request, UploadFile, HTTPException
from pydantic import BaseModel, Field

from app.services.tesseract_engine import TesseractOCREngine
from app.services.easyocr_engine import EasyOCREngine
from app.services.pdf_extractor import PDFExtractor
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()

# Initialize engines
tesseract_engine = TesseractOCREngine()
easyocr_engine = EasyOCREngine()
pdf_extractor = PDFExtractor()


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x1: int = Field(..., description="Top-left x coordinate")
    y1: int = Field(..., description="Top-left y coordinate")
    x2: int = Field(..., description="Bottom-right x coordinate")
    y2: int = Field(..., description="Bottom-right y coordinate")


class Region(BaseModel):
    """Text region within a page."""

    text: str = Field(..., description="Extracted text from region")
    bounding_box: list[int] = Field(
        ..., description="Bounding box [x1, y1, x2, y2]"
    )
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    type: str = Field(default="paragraph", description="Region type")


class Page(BaseModel):
    """Extracted page data."""

    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    text: str = Field(..., description="Full page text")
    regions: list[Region] = Field(default_factory=list, description="Text regions")


class OCRResponse(BaseModel):
    """OCR API response."""

    text: str = Field(..., description="Full extracted text")
    pages: list[Page] = Field(default_factory=list, description="Per-page data")
    language: str = Field(..., description="Detected/specified language")
    engine_used: str = Field(..., description="OCR engine used (tesseract|easyocr)")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


@router.post("", response_model=OCRResponse)
async def ocr_process(
    request: Request,
    file: UploadFile = File(...),
    languages: str = Form(default="hin+eng"),
    engine: str = Form(default="auto"),
) -> OCRResponse:
    """
    Process a single document (image or PDF) with OCR.

    Args:
        file: Image (PNG/JPG) or PDF file
        languages: Comma or plus-separated language codes (e.g., "hi,en" or "hin+eng")
        engine: OCR engine to use ("auto" | "tesseract" | "easyocr")

    Returns:
        OCRResponse with extracted text, regions, confidence scores
    """
    import time
    from io import BytesIO

    request_id = getattr(request.state, "request_id", "unknown")
    start_time = time.time()

    try:
        # Validate file size
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)

        if file_size_mb > settings.max_image_size_mb:
            logger.warning(
                "file_too_large",
                file_size_mb=file_size_mb,
                max_size_mb=settings.max_image_size_mb,
                request_id=request_id,
            )
            raise HTTPException(
                status_code=413,
                detail={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": f"File exceeds maximum size of {settings.max_image_size_mb}MB",
                        "request_id": request_id,
                    }
                },
            )

        # Determine file type
        file_extension = file.filename.split(".")[-1].lower()
        is_pdf = file_extension == "pdf" or file.content_type == "application/pdf"

        logger.info(
            "ocr_request_received",
            filename=file.filename,
            file_size_mb=file_size_mb,
            is_pdf=is_pdf,
            languages=languages,
            engine=engine,
            request_id=request_id,
        )

        # Extract pages from PDF if needed
        if is_pdf:
            pages_data = pdf_extractor.extract_pages(
                BytesIO(contents), settings.target_dpi
            )
            if not pages_data:
                raise ValueError("Failed to extract pages from PDF")
        else:
            # Single image
            from PIL import Image

            image = Image.open(BytesIO(contents))
            pages_data = [{"image": image, "page_number": 1}]

        # Perform OCR on each page
        all_pages = []
        all_text_parts = []
        confidences = []

        for page_data in pages_data:
            if len(all_pages) >= settings.max_pdf_pages:
                logger.warning(
                    "pdf_page_limit_exceeded",
                    max_pages=settings.max_pdf_pages,
                    request_id=request_id,
                )
                break

            page_image = page_data["image"]
            page_num = page_data.get("page_number", len(all_pages) + 1)

            # Choose and run OCR engine
            if engine == "auto":
                # Try Tesseract first, fall back to EasyOCR if it fails
                try:
                    page_result = tesseract_engine.process(
                        page_image, languages, page_num
                    )
                    engine_used = "tesseract"
                except Exception as e:
                    logger.warning(
                        "tesseract_fallback",
                        error=str(e),
                        page_number=page_num,
                        request_id=request_id,
                    )
                    page_result = easyocr_engine.process(
                        page_image, languages, page_num
                    )
                    engine_used = "easyocr"
            elif engine == "easyocr":
                page_result = easyocr_engine.process(page_image, languages, page_num)
                engine_used = "easyocr"
            else:  # tesseract
                page_result = tesseract_engine.process(page_image, languages, page_num)
                engine_used = "tesseract"

            all_pages.append(page_result)
            all_text_parts.append(page_result["text"])
            if page_result.get("confidence"):
                confidences.append(page_result["confidence"])

        # Combine results
        full_text = "\n\n".join(all_text_parts)
        overall_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Detect primary language (simplified: check if more Hindi chars)
        detected_language = (
            "hi" if full_text.count("\u0900") > len(full_text) * 0.1 else "en"
        )

        response = OCRResponse(
            text=full_text,
            pages=[
                Page(
                    page_number=p["page_number"],
                    text=p["text"],
                    regions=[
                        Region(
                            text=r["text"],
                            bounding_box=r["bounding_box"],
                            confidence=r["confidence"],
                            type=r.get("type", "paragraph"),
                        )
                        for r in p.get("regions", [])
                    ],
                )
                for p in all_pages
            ],
            language=detected_language,
            engine_used=engine_used,
            confidence=overall_confidence,
            processing_time_ms=processing_time_ms,
        )

        logger.info(
            "ocr_request_completed",
            num_pages=len(all_pages),
            confidence=overall_confidence,
            processing_time_ms=processing_time_ms,
            engine_used=engine_used,
            request_id=request_id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "ocr_request_failed",
            error=str(e),
            error_type=type(e).__name__,
            request_id=request_id,
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "PROCESSING_FAILED",
                    "message": f"OCR processing failed: {str(e)}",
                    "request_id": request_id,
                }
            },
        )
