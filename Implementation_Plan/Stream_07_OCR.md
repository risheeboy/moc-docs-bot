### STREAM 7: OCR & Document Processing Service

**Agent Goal:** Build the OCR pipeline for digitizing Hindi and English documents from scanned images/PDFs.

**Files to create:**
```
ocr-service/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── config.py                   # OCR engine settings, language packs
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ocr.py                  # POST /ocr (image/PDF → text)
│   │   ├── batch.py                # POST /ocr/batch (multiple files)
│   │   └── health.py               # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tesseract_engine.py     # Tesseract OCR (Hindi + English)
│   │   ├── easyocr_engine.py       # EasyOCR (better Hindi handwriting)
│   │   ├── preprocessor.py         # Image preprocessing (deskew, denoise, binarize)
│   │   ├── pdf_extractor.py        # Extract pages from PDF as images
│   │   ├── postprocessor.py        # OCR text cleanup, Hindi ligature fixes
│   │   └── layout_analyzer.py      # Detect text regions, tables, headers
│   └── utils/
│       ├── __init__.py
│       └── metrics.py
├── tessdata/                       # Trained Tesseract data for Hindi
│   └── .gitkeep
└── tests/
    ├── test_ocr_hindi.py
    ├── test_ocr_english.py
    └── fixtures/
        ├── sample_hindi_scan.png
        └── sample_bilingual.pdf
```

**No code dependencies on other streams.**

---


---

## Agent Prompt

### Agent 7: OCR Service
```
Build a FastAPI OCR service with: Tesseract 5 (Hindi+English), EasyOCR fallback
for degraded text, OpenCV preprocessing (deskew, denoise, binarize),
PDF page extraction, text post-processing for Hindi ligatures.
Output structured JSON with text, bounding boxes, confidence scores.
```

