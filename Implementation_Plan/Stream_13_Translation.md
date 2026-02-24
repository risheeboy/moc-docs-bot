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

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: this service runs on port 8004 as `translation-service`
- §3 Environment Variables: read `TRANSLATION_*`, `REDIS_*` (DB 3 for translation cache) variables
- §4 Error Response Format: use standard error format; use `INVALID_LANGUAGE` for unsupported pairs
- §5 Health Check Format: `/health` must check GPU and Redis connectivity
- §8.4 API Contract: implement exact `/translate`, `/translate/batch`, `/detect` schemas from §8.4
- §9 Language Codes: support all 23 codes from §9
- §11 Prometheus Metrics: expose `translation_duration_seconds`, `translation_cache_hit_total`

---


---

## Agent Prompt

### Agent 13: Translation Service (**NEW**)
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Port 8004. Use exact API schemas from §8.4, all 23 language codes from §9.
Redis DB 3 for cache per §3.2.
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

