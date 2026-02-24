# Translation Service

FastAPI on port 8004. Translation service for 22 Indian languages via AI4Bharat IndicTrans2 (CPU-based).

## Key Files

- `app/main.py` — FastAPI application
- `app/services/translator.py` — IndicTrans2 inference wrapper
- `app/services/cache.py` — Redis translation caching (24h TTL)
- `app/routers/translate.py` — Translation endpoints
- `app/config.py` — Model and cache configuration

## Endpoints

- `POST /translate` — Single translation (text, source_lang, target_lang)
- `POST /translate/batch` — Batch translations (same language pair)
- `GET /languages` — List 22 supported languages
- `GET /health` — Health check

## Supported Languages

22 Indian languages: Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, and 11 others (see contracts §9).

## Caching

- Key: SHA256(text + source_lang + target_lang)
- TTL: 24 hours
- Reduces latency for repeated translations

## Model

- IndicTrans2 (1B parameters)
- AI4Bharat pre-trained + fine-tuned on Indian corpora
- CPU inference (GPU optional)

## Dependencies

- transformers library
- IndicTrans2 model weights
- Redis (caching)
- tokenizers

## Known Issues

None critical. Service is stable.
