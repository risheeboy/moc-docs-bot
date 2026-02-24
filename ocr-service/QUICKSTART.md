# Quick Start Guide - OCR Service

Get the OCR service running in 5 minutes.

## Option 1: Docker (Recommended)

```bash
# Build
docker build -t ocr-service:latest .

# Run
docker run -p 8005:8005 ocr-service:latest

# Test
curl -X POST http://localhost:8005/health
```

## Option 2: Local Development

```bash
# Prerequisites: Python 3.11+, Tesseract 5
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-hin poppler-utils

# macOS (with Homebrew):
brew install tesseract tesseract-lang poppler

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

## Testing the Service

### Health Check
```bash
curl http://localhost:8005/health | jq
```

### Single File OCR
```bash
# With image
curl -X POST http://localhost:8005/ocr \
  -F "file=@tests/fixtures/sample_english_scan.png" \
  -F "languages=en" \
  -F "engine=auto" | jq

# With PDF
curl -X POST http://localhost:8005/ocr \
  -F "file=@tests/fixtures/sample_bilingual.pdf" \
  -F "languages=hin+eng" \
  -F "engine=auto" | jq
```

### Batch OCR
```bash
curl -X POST http://localhost:8005/ocr/batch \
  -F "files=@tests/fixtures/sample_english_scan.png" \
  -F "files=@tests/fixtures/sample_hindi_scan.png" \
  -F "languages=hin+eng" | jq
```

### Metrics
```bash
curl http://localhost:8005/metrics
```

## Configuration

Key environment variables:

```bash
# Engine selection
OCR_TESSERACT_LANG=hin+eng        # Languages for Tesseract
OCR_EASYOCR_LANGS=hi,en            # Languages for EasyOCR

# Processing
OCR_ENABLE_PREPROCESSING=true
OCR_DESKEW_ENABLED=true
OCR_DENOISE_ENABLED=true
OCR_BINARIZE_ENABLED=true

# Limits
OCR_MAX_IMAGE_SIZE_MB=50
OCR_MAX_PDF_PAGES=500
OCR_TARGET_DPI=300

# Logging
APP_LOG_LEVEL=INFO
APP_DEBUG=false
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_ocr_hindi.py -v

# With coverage
pytest tests/ --cov=app

# Fast tests only (skip slow)
pytest tests/ -m "not slow"
```

## Project Structure

```
ocr-service/
├── app/
│   ├── main.py              ← FastAPI app
│   ├── config.py            ← Settings
│   ├── routers/
│   │   ├── ocr.py           ← Single file OCR
│   │   ├── batch.py         ← Batch processing
│   │   └── health.py        ← Health check
│   ├── services/
│   │   ├── tesseract_engine.py   ← Tesseract OCR
│   │   ├── easyocr_engine.py     ← EasyOCR fallback
│   │   ├── preprocessor.py       ← Image preprocessing
│   │   ├── pdf_extractor.py      ← PDF handling
│   │   ├── postprocessor.py      ← Text cleanup
│   │   └── layout_analyzer.py    ← Layout detection
│   └── utils/
│       └── metrics.py       ← Prometheus metrics
├── tests/
│   ├── test_ocr_hindi.py
│   ├── test_ocr_english.py
│   └── fixtures/            ← Test images/PDFs
├── Dockerfile
├── requirements.txt
└── README.md
```

## Common Tasks

### Test with Your Own Document
```bash
curl -X POST http://localhost:8005/ocr \
  -F "file=@/path/to/your/document.pdf" \
  -F "languages=hin+eng" \
  -F "engine=auto"
```

### Process Multiple Documents
```bash
curl -X POST http://localhost:8005/ocr/batch \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.jpg" \
  -F "files=@doc3.png" \
  -F "languages=hin+eng"
```

### Change Processing Engine
```bash
# Force Tesseract
curl -X POST http://localhost:8005/ocr \
  -F "file=@document.pdf" \
  -F "engine=tesseract"

# Force EasyOCR
curl -X POST http://localhost:8005/ocr \
  -F "file=@document.pdf" \
  -F "engine=easyocr"

# Auto (try Tesseract, fallback to EasyOCR)
curl -X POST http://localhost:8005/ocr \
  -F "file=@document.pdf" \
  -F "engine=auto"
```

### Get Detailed Output
```bash
curl -X POST http://localhost:8005/ocr \
  -F "file=@document.pdf" \
  -F "languages=hin+eng" | jq '.pages[0].regions'
```

## Troubleshooting

### Tesseract Not Found
```bash
# On Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-hin

# On macOS
brew install tesseract tesseract-lang

# Verify installation
tesseract --version
```

### Hindi Language Pack Missing
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr-hin

# macOS
brew install tesseract-lang
```

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use
```bash
# Change port
uvicorn app.main:app --host 0.0.0.0 --port 8006

# Or kill process using port 8005
lsof -i :8005
kill -9 <PID>
```

## Next Steps

1. **Read** `README.md` for complete documentation
2. **Review** `IMPLEMENTATION_SUMMARY.md` for implementation details
3. **Explore** test files to understand usage patterns
4. **Check** API endpoint documentation in README.md §2

## Integration with RAG System

The OCR service is called by the API Gateway at:
```
http://ocr-service:8005/ocr
http://ocr-service:8005/ocr/batch
```

See `01_Shared_Contracts.md` §8.5 for complete API contract.

## Performance Tips

- **Single engine**: Use "tesseract" for speed, "easyocr" for accuracy
- **Preprocessing**: Disable if not needed (faster but less accurate)
- **DPI**: Lower DPI for speed, higher for accuracy (default 300)
- **Batch**: Process multiple files together for better resource utilization

## Getting Help

- Check logs: `docker logs <container-id>`
- Health check: `curl http://localhost:8005/health`
- Metrics: `curl http://localhost:8005/metrics`
- Tests: `pytest tests/ -v` for validation

Happy OCRing! 🚀
