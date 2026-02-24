# OCR Service

FastAPI on port 8005. Optical character recognition with dual engines (Tesseract 5 + EasyOCR) for Hindi/Indian documents.

## Key Files

- `app/main.py` — FastAPI application
- `app/services/ocr_engine.py` — Dual engine coordination
- `app/services/preprocessor.py` — Image preprocessing (binarization, deskew, noise removal)
- `app/services/layout_analyzer.py` — Multi-column detection
- `app/config.py` — Engine configuration

## Endpoints

- `POST /ocr/extract` — Extract text from image/PDF
- `POST /ocr/batch` — Batch process multiple images
- `GET /languages` — List supported languages
- `GET /health` — Health check

## Supported Languages

Hindi (primary), English, 10 other Indian languages (incomplete, see Known Issues).

## Preprocessing Pipeline

1. Binarization (Otsu's method)
2. Deskew (rotation correction)
3. Noise removal (morphological)
4. Contrast enhancement

## Engines

- **Tesseract 5** — Primary, fast, reliable for printed text
- **EasyOCR** — Fallback, slower, handles handwriting and complex fonts

## Dependencies

- Tesseract 5+ (system: tesseract-ocr)
- EasyOCR (Python)
- OpenCV (image processing)
- Pillow (image I/O)
- pytesseract (wrapper)

## Known Issues

1. **Incomplete language mapping** — Only 12 of 22 languages. Missing: Maithili, Sanskrit, others.
2. **CORS misconfiguration** — Uses `allow_origins=["*"]`. Fix: restrict to ALB.
3. **No confidence scoring** — Doesn't report OCR confidence per word/line.
4. **No table detection** — Multi-column tables may reconstruct incorrectly.
