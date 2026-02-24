"""Batch OCR router for processing multiple files."""

from typing import Optional
import uuid
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

# In-memory batch job tracking (in production, use Redis or database)
batch_jobs = {}


class BatchResult(BaseModel):
    """Result for a single file in batch."""

    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="success | failed")
    text: Optional[str] = Field(default=None, description="Extracted text")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    confidence: Optional[float] = Field(default=None, description="Confidence score")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time")


class BatchResponse(BaseModel):
    """Batch OCR response."""

    batch_id: str = Field(..., description="Unique batch ID")
    status: str = Field(..., description="completed | partial | failed")
    results: list[BatchResult] = Field(..., description="Per-file results")
    total_files: int = Field(..., description="Total files in batch")
    successful: int = Field(..., description="Successfully processed files")
    failed: int = Field(..., description="Failed files")
    total_processing_time_ms: float = Field(..., description="Total processing time")


@router.post("", response_model=BatchResponse)
async def batch_ocr_process(
    request: Request,
    files: list[UploadFile] = File(...),
    languages: str = Form(default="hin+eng"),
    engine: str = Form(default="auto"),
) -> BatchResponse:
    """
    Process multiple documents (images or PDFs) with OCR.

    Args:
        files: List of image (PNG/JPG) or PDF files
        languages: Comma or plus-separated language codes (e.g., "hi,en" or "hin+eng")
        engine: OCR engine to use ("auto" | "tesseract" | "easyocr")

    Returns:
        BatchResponse with results for each file
    """
    import time
    from io import BytesIO

    request_id = getattr(request.state, "request_id", "unknown")
    batch_id = str(uuid.uuid4())
    start_time = time.time()

    if not files:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "No files provided",
                    "request_id": request_id,
                }
            },
        )

    if len(files) > settings.max_batch_size:
        raise HTTPException(
            status_code=413,
            detail={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Batch size exceeds maximum of {settings.max_batch_size}",
                    "request_id": request_id,
                }
            },
        )

    logger.info(
        "batch_ocr_request_received",
        batch_id=batch_id,
        num_files=len(files),
        languages=languages,
        engine=engine,
        request_id=request_id,
    )

    results = []
    successful = 0
    failed = 0

    for file in files:
        file_start = time.time()

        try:
            # Read file
            contents = await file.read()
            file_size_mb = len(contents) / (1024 * 1024)

            if file_size_mb > settings.max_image_size_mb:
                logger.warning(
                    "batch_file_too_large",
                    filename=file.filename,
                    file_size_mb=file_size_mb,
                    batch_id=batch_id,
                    request_id=request_id,
                )
                results.append(
                    BatchResult(
                        filename=file.filename,
                        status="failed",
                        error=f"File exceeds maximum size of {settings.max_image_size_mb}MB",
                    )
                )
                failed += 1
                continue

            # Determine file type
            file_extension = file.filename.split(".")[-1].lower()
            is_pdf = file_extension == "pdf" or file.content_type == "application/pdf"

            # Extract pages
            if is_pdf:
                pages_data = pdf_extractor.extract_pages(
                    BytesIO(contents), settings.target_dpi
                )
                if not pages_data:
                    raise ValueError("Failed to extract pages from PDF")
            else:
                from PIL import Image

                image = Image.open(BytesIO(contents))
                pages_data = [{"image": image, "page_number": 1}]

            # Perform OCR
            all_text_parts = []
            confidences = []

            for page_data in pages_data[: settings.max_pdf_pages]:
                page_image = page_data["image"]

                if engine == "auto":
                    try:
                        page_result = tesseract_engine.process(
                            page_image, languages, 1
                        )
                    except Exception:
                        page_result = easyocr_engine.process(page_image, languages, 1)
                elif engine == "easyocr":
                    page_result = easyocr_engine.process(page_image, languages, 1)
                else:
                    page_result = tesseract_engine.process(page_image, languages, 1)

                all_text_parts.append(page_result["text"])
                if page_result.get("confidence"):
                    confidences.append(page_result["confidence"])

            full_text = "\n\n".join(all_text_parts)
            overall_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            file_processing_time = (time.time() - file_start) * 1000

            results.append(
                BatchResult(
                    filename=file.filename,
                    status="success",
                    text=full_text,
                    confidence=overall_confidence,
                    processing_time_ms=file_processing_time,
                )
            )
            successful += 1

            logger.info(
                "batch_file_processed",
                filename=file.filename,
                confidence=overall_confidence,
                processing_time_ms=file_processing_time,
                batch_id=batch_id,
                request_id=request_id,
            )

        except Exception as e:
            logger.error(
                "batch_file_failed",
                filename=file.filename,
                error=str(e),
                batch_id=batch_id,
                request_id=request_id,
            )
            results.append(
                BatchResult(
                    filename=file.filename, status="failed", error=str(e)
                )
            )
            failed += 1

    total_time_ms = (time.time() - start_time) * 1000

    batch_status = "completed" if failed == 0 else ("partial" if successful > 0 else "failed")

    response = BatchResponse(
        batch_id=batch_id,
        status=batch_status,
        results=results,
        total_files=len(files),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_time_ms,
    )

    logger.info(
        "batch_ocr_completed",
        batch_id=batch_id,
        status=batch_status,
        successful=successful,
        failed=failed,
        total_time_ms=total_time_ms,
        request_id=request_id,
    )

    return response
