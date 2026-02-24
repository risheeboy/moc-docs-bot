### STREAM 13: Translation Service (IndicTrans2) (**NEW**)

**Agent Goal:** Build the dedicated translation microservice wrapping **AI4Bharat IndicTrans2** for translating between all 22 scheduled Indian languages + English.

**Files to create:**
```
translation-service/
├── Dockerfile                      # python:3.11-slim + CUDA
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── config.py                   # Model paths, supported language pairs
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── translate.py            # POST /translate (text → translated text)
│   │   ├── batch_translate.py      # POST /translate/batch (multiple texts)
│   │   ├── detect_language.py      # POST /detect (auto-detect language)
│   │   └── health.py               # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── indictrans2_engine.py   # IndicTrans2 model loading + inference
│   │   ├── language_detector.py    # AI4Bharat language identification
│   │   ├── script_converter.py     # Transliteration between scripts (Devanagari ↔ Latin etc.)
│   │   └── cache.py                # Redis-backed translation cache (avoid re-translating)
│   └── utils/
│       ├── __init__.py
│       └── metrics.py
├── model-download.sh               # Download IndicTrans2 model weights
└── tests/
    ├── test_translate.py
    ├── test_hindi_english.py
    └── test_batch.py
```

**Key technical decisions (from Design):**
- **IndicTrans2** — AI4Bharat's open-source translation model supporting all 22 scheduled Indian languages
- **Caching** — Redis-backed cache keyed on (source_text_hash, source_lang, target_lang) to avoid redundant translations
- **Batch API** — for translating search results or document chunks in bulk
- **Used by:** Search page (translate results), Chatbot (translate responses), Data Ingestion (language classification)

**Requires:** GPU for IndicTrans2 inference. No code dependencies on other streams.

---


---

## Agent Prompt

### Agent 13: Translation Service (**NEW**)
```
Build a FastAPI translation microservice wrapping AI4Bharat IndicTrans2.
- POST /translate (single text translation between any pair of 22 scheduled
  Indian languages + English)
- POST /translate/batch (bulk translation for search results)
- POST /detect (auto-detect input language)
- Redis-backed translation cache (hash-keyed to avoid re-translating)
- Script transliteration (Devanagari ↔ Latin etc.)
- GPU required for IndicTrans2 inference
- Pre-download model weights script
```

