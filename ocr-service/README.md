# OCR Service - Stream 7

FastAPI-based OCR (Optical Character Recognition) service for digitizing Hindi and English documents. Part of the RAG-based Hindi QA system for India's Ministry of Culture.

## Features

- **Multi-engine support**: Tesseract 5 (primary) + EasyOCR (fallback)
- **Language support**: Hindi (Devanagari) and English
- **PDF & Image processing**: Extract text from images (PNG/JPG) and PDFs
- **Image preprocessing**: Deskew, denoise, and binarize for improved accuracy
- **Layout analysis**: Detect text regions, tables, headers, and columns
- **Post-processing**: Hindi ligature fixes, English OCR error corrections
- **Batch processing**: Process multiple files in a single request
- **Confidence scoring**: Per-region and per-page confidence metrics
- **Prometheus metrics**: Full observability and monitoring

## Architecture

```
OCR Service (Port 8005)
├── Tesseract Engine (Hindi + English)
├── EasyOCR Engine (Fallback for degraded/handwritten text)
├── Image Preprocessor (Deskew, Denoise, Binarize, Upscale)
├── PDF Extractor (Page extraction at configurable DPI)
├── Layout Analyzer (Region, table, header, column detection)
├── Post-Processor (Text cleanup, language-specific fixes)
└── Metrics (Prometheus counters and histograms)
```

## API Endpoints

### Single File OCR

**POST** `/ocr`

Upload a single image or PDF for OCR processing.

**Request:**
```bash
curl -X POST http://localhost:8005/ocr \
  -F "file=@document.pdf" \
  -F "languages=hin+eng" \
  -F "engine=auto"
```

**Parameters:**
- `file` (required): Image (PNG/JPG) or PDF file
- `languages` (optional): Language codes, comma or plus-separated (default: "hin+eng")
  - "hi" or "hin" for Hindi
  - "en" or "eng" for English
- `engine` (optional): "auto" | "tesseract" | "easyocr" (default: "auto")

**Response:**
```json
{
  "text": "Full extracted text...",
  "pages": [
    {
      "page_number": 1,
      "text": "Page 1 text...",
      "regions": [
        {
          "text": "Region text",
          "bounding_box": [x1, y1, x2, y2],
          "confidence": 0.89,
          "type": "paragraph"
        }
      ]
    }
  ],
  "language": "hi",
  "engine_used": "tesseract",
  "confidence": 0.87,
  "processing_time_ms": 1234.5
}
```

### Batch OCR Processing

**POST** `/ocr/batch`

Process multiple files in a single request.

**Request:**
```bash
curl -X POST http://localhost:8005/ocr/batch \
  -F "files=@file1.pdf" \
  -F "files=@file2.png" \
  -F "languages=hin+eng" \
  -F "engine=auto"
```

**Response:**
```json
{
  "batch_id": "uuid",
  "status": "completed",
  "results": [
    {
      "filename": "file1.pdf",
      "status": "success",
      "text": "Extracted text...",
      "confidence": 0.89,
      "processing_time_ms": 1234.5
    },
    {
      "filename": "file2.png",
      "status": "success",
      "text": "Extracted text...",
      "confidence": 0.92,
      "processing_time_ms": 567.2
    }
  ],
  "total_files": 2,
  "successful": 2,
  "failed": 0,
  "total_processing_time_ms": 1801.7
}
```

### Health Check

**GET** `/health`

Check service health status and dependencies.

**Response:**
```json
{
  "status": "healthy",
  "service": "ocr-service",
  "version": "1.0.0",
  "uptime_seconds": 3612.5,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "tesseract": { "status": "healthy", "latency_ms": 12.3 },
    "easyocr": { "status": "healthy", "latency_ms": 45.6 }
  }
}
```

### Metrics

**GET** `/metrics`

Prometheus metrics endpoint for monitoring.

## Configuration

Environment variables (from `.env` or Docker environment):

```bash
# Service
APP_ENV=production                    # production | staging | development
APP_DEBUG=false
APP_LOG_LEVEL=INFO                    # DEBUG | INFO | WARNING | ERROR

# OCR Engines
OCR_TESSERACT_LANG=hin+eng            # Tesseract languages
OCR_EASYOCR_LANGS=hi,en               # EasyOCR languages

# Processing
TESSERACT_DESKEW_ENABLED=true
TESSERACT_DENOISE_ENABLED=true
TESSERACT_BINARIZE_ENABLED=true

# Limits
OCR_MAX_IMAGE_SIZE_MB=50
OCR_MAX_PDF_PAGES=500
OCR_TARGET_DPI=300

# Timeouts
OCR_OCR_TIMEOUT_SECONDS=300
OCR_PDF_EXTRACTION_TIMEOUT_SECONDS=120

# Batch
OCR_MAX_BATCH_SIZE=100
OCR_BATCH_TIMEOUT_SECONDS=600
```

## Installation

### Local Development

```bash
# Clone and navigate to service directory
cd ocr-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-hin poppler-utils

# Run tests
pytest tests/

# Run locally
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### Docker

```bash
# Build image
docker build -t ocr-service:latest .

# Run container
docker run -p 8005:8005 \
  -e OCR_TESSERACT_LANG=hin+eng \
  -e APP_LOG_LEVEL=INFO \
  ocr-service:latest
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ocr_hindi.py -v

# Run with coverage
pytest --cov=app tests/

# Run only unit tests
pytest -m unit

# Run specific test
pytest tests/test_ocr_hindi.py::TestTesseractOCREngine::test_engine_initialization -v
```

## Project Structure

```
ocr-service/
├── Dockerfile                    # Docker configuration
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration and settings
│   ├── routers/
│   │   ├── health.py             # Health check endpoint
│   │   ├── ocr.py                # Single file OCR endpoint
│   │   └── batch.py              # Batch processing endpoint
│   ├── services/
│   │   ├── tesseract_engine.py   # Tesseract OCR engine
│   │   ├── easyocr_engine.py     # EasyOCR fallback engine
│   │   ├── preprocessor.py       # Image preprocessing
│   │   ├── pdf_extractor.py      # PDF page extraction
│   │   ├── postprocessor.py      # Text cleanup and fixes
│   │   └── layout_analyzer.py    # Layout detection
│   └── utils/
│       └── metrics.py            # Prometheus metrics
├── tessdata/                     # Tesseract trained data
├── tests/
│   ├── test_ocr_hindi.py        # Hindi OCR tests
│   ├── test_ocr_english.py      # English OCR tests
│   └── fixtures/
│       ├── sample_hindi_scan.png
│       ├── sample_english_scan.png
│       └── sample_bilingual.pdf
└── README.md
```

## Service Integration

The OCR service integrates with other services in the system:

- **Called by**: API Gateway (`/ocr` endpoint)
- **Calls**: None (standalone service)
- **Data flows**: Receives raw documents, outputs extracted text with metadata

### Inter-service API Contract

See `01_Shared_Contracts.md` §8.5 for the complete API schema.

## Performance Characteristics

- **Single image (PNG/JPG, 300 DPI)**: ~1-5 seconds (depending on OCR engine)
- **Multi-page PDF**: ~2-10 seconds (depends on page count)
- **Max file size**: 50 MB
- **Max batch size**: 100 files
- **Concurrent requests**: Limited by container resources

## Error Handling

All errors follow the standard error format from §4 of `01_Shared_Contracts.md`:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

Common error codes:
- `INVALID_REQUEST`: Malformed request
- `PAYLOAD_TOO_LARGE`: File exceeds size limit
- `PROCESSING_FAILED`: OCR processing error
- `INTERNAL_ERROR`: Unexpected server error

## Monitoring

Prometheus metrics are exposed at `/metrics`:

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `http_request_size_bytes`: Request body size
- `http_response_size_bytes`: Response body size
- `ocr_processing_duration_seconds`: OCR processing time
- `ocr_files_processed_total`: Total files processed
- `ocr_confidence_histogram`: Confidence score distribution
- `ocr_engine_errors_total`: Total errors per engine

## Known Limitations

1. Handwritten text recognition is limited; EasyOCR provides better results for degraded/handwritten text
2. Very small text (<8pt) may have reduced accuracy
3. Skewed or rotated text requires preprocessing (automatic deskewing is enabled by default)
4. Multi-column layouts may require additional layout analysis
5. Table recognition is basic; complex table structures may need post-processing

## Future Enhancements

- [ ] Support for more Indic languages
- [ ] Fine-tuned models for Ministry-specific documents
- [ ] Table extraction and structure preservation
- [ ] Form field detection and extraction
- [ ] Handwriting recognition improvements
- [ ] GPU acceleration for EasyOCR
- [ ] Incremental processing for large PDFs
- [ ] Caching for repeated documents

## Dependencies

- **Tesseract 5**: Open-source OCR engine
- **EasyOCR**: Deep learning-based OCR
- **Pillow**: Image processing
- **OpenCV**: Computer vision preprocessing
- **pdf2image**: PDF to image conversion
- **pytesseract**: Python wrapper for Tesseract
- **FastAPI**: Web framework
- **Prometheus Client**: Metrics collection

## License

Part of the RAG-based Hindi QA system for India's Ministry of Culture.

## Support

For issues or questions about the OCR service, refer to the main project documentation or contact the development team.
