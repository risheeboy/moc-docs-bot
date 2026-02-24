# API Gateway Endpoints Reference

All endpoints are prefixed with `/api/v1`

## Health & Monitoring

| Method | Endpoint | Description | Auth | Interface |
|--------|----------|-------------|------|-----------|
| GET | `/health` | Health check (aggregates all services) | None | Internal |
| GET | `/metrics` | Prometheus metrics | None | Monitoring |
| GET | `/` | API info + doc links | None | Public |

## Chat (Conversational Interface)

| Method | Endpoint | Description | Auth | Body Schema |
|--------|----------|-------------|------|------------|
| POST | `/chat` | Single chat query with RAG context | JWT/API-Key | ChatRequest |
| POST | `/chat/stream` | Streaming chat response (SSE) | JWT/API-Key | ChatRequest |

**ChatRequest:**
```json
{
  "query": "string (1-2000 chars)",
  "language": "en|hi|...",
  "session_id": "uuid (optional)",
  "chat_history": [{"role": "user|assistant", "content": "string"}],
  "top_k": "integer (1-50, default 10)",
  "filters": {
    "source_sites": ["string[]"],
    "content_type": "string|null",
    "date_from": "string|null",
    "date_to": "string|null"
  }
}
```

**ChatResponse:**
```json
{
  "response": "string",
  "sources": [{"title": "string", "url": "string", "score": 0.95, ...}],
  "confidence": 0.85,
  "session_id": "uuid",
  "language": "en",
  "model_used": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "cached": false,
  "request_id": "uuid",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

## Search (Unified Semantic Search)

| Method | Endpoint | Description | Auth | Query Params |
|--------|----------|-------------|------|--------------|
| GET | `/search` | Unified search with AI summaries + multimedia | JWT/API-Key | query, language, page, page_size |
| GET | `/search/suggest` | Auto-complete suggestions | JWT/API-Key | prefix, language, limit |

**Query Parameters for /search:**
- `query` (required): Search term (1-2000 chars)
- `language` (default: "en"): ISO language code
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Results per page

**SearchResponse:**
```json
{
  "results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "score": 0.95,
      "source_site": "string",
      "language": "en",
      "content_type": "webpage|pdf|...",
      "ai_summary": "string (optional)",
      "published_date": "2025-06-15"
    }
  ],
  "multimedia": [
    {"type": "image|video", "url": "string", "alt_text": "string", ...}
  ],
  "events": [
    {"title": "string", "date": "2026-03-15", "venue": "string", ...}
  ],
  "total_results": 142,
  "page": 1,
  "page_size": 20,
  "cached": false,
  "request_id": "uuid",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

## Voice (Speech I/O)

| Method | Endpoint | Description | Auth | Content-Type |
|--------|----------|-------------|------|--------------|
| POST | `/voice/stt` | Speech-to-text (audio → text) | JWT/API-Key | multipart/form-data |
| POST | `/voice/tts` | Text-to-speech (text → audio) | JWT/API-Key | application/x-www-form-urlencoded |

**STT:**
- Form field: `file` (required) - Audio file (WAV/MP3/WebM/OGG)
- Form field: `language` (optional) - "hi", "en", or "auto" (default)

**STT Response:**
```json
{
  "text": "Transcribed text here",
  "language": "hi",
  "confidence": 0.94,
  "duration_seconds": 3.5,
  "request_id": "uuid",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

**TTS:**
- Form field: `text` (required) - Text to synthesize (1-5000 chars)
- Form field: `language` (default: "en")
- Form field: `format` (default: "mp3") - "mp3", "wav", "ogg"
- Form field: `voice` (default: "default")

**TTS Response:** Binary audio data with headers:
- `X-Duration-Seconds`: Audio length
- `X-Language`: Language code

## Translation

| Method | Endpoint | Description | Auth | Body Schema |
|--------|----------|-------------|------|------------|
| POST | `/translate` | Translate single text | JWT/API-Key | TranslateRequest |
| POST | `/translate/batch` | Translate multiple texts | JWT/API-Key | TranslateBatchRequest |
| POST | `/translate/detect` | Detect language | JWT/API-Key | DetectRequest |

**TranslateRequest:**
```json
{
  "text": "string (1-10000 chars)",
  "source_language": "en",
  "target_language": "hi"
}
```

**TranslateResponse:**
```json
{
  "translated_text": "string",
  "source_language": "en",
  "target_language": "hi",
  "cached": true,
  "request_id": "uuid",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

## Document Management

| Method | Endpoint | Description | Auth | Content-Type |
|--------|----------|-------------|------|--------------|
| POST | `/documents/upload` | Upload document for ingestion | JWT (admin/editor) | multipart/form-data |
| GET | `/documents` | List ingested documents | JWT/API-Key | — |
| DELETE | `/documents/{id}` | Delete document + cleanup | JWT (admin/editor) | — |

**Upload:**
- Form field: `file` (required) - PDF/TXT/DOCX
- Form field: `title` (required) - Document title
- Form field: `description` (optional)
- Form field: `source_url` (optional)
- Form field: `language` (default: "en")

**DocumentResponse:**
```json
{
  "document_id": "uuid",
  "title": "string",
  "source_url": "string (optional)",
  "language": "en",
  "content_type": "pdf|text|...",
  "chunk_count": 12,
  "embedding_status": "completed|pending|failed",
  "created_at": "2026-02-24T10:30:00Z",
  "updated_at": "2026-02-24T10:30:00Z",
  "request_id": "uuid"
}
```

## Feedback

| Method | Endpoint | Description | Auth | Body Schema |
|--------|----------|-------------|------|------------|
| POST | `/feedback` | Submit user feedback | JWT/API-Key | FeedbackCreate |

**FeedbackCreate:**
```json
{
  "session_id": "uuid",
  "query": "string (1-2000 chars)",
  "response": "string (1-5000 chars)",
  "rating": 1-5,
  "feedback_text": "string (optional, max 2000)",
  "feedback_type": "chat|search",
  "language": "en"
}
```

**FeedbackResponse:**
```json
{
  "feedback_id": "uuid",
  "session_id": "uuid",
  "rating": 5,
  "feedback_type": "chat",
  "sentiment_score": 0.85,
  "sentiment_label": "positive|neutral|negative",
  "created_at": "2026-02-24T10:30:00Z",
  "request_id": "uuid"
}
```

## OCR (Optical Character Recognition)

| Method | Endpoint | Description | Auth | Content-Type |
|--------|----------|-------------|------|--------------|
| POST | `/ocr/upload` | Extract text from image/PDF | JWT (admin/editor) | multipart/form-data |

**Upload:**
- Form field: `file` (required) - PNG/JPG/PDF
- Form field: `languages` (default: "hi,en") - Comma-separated
- Form field: `engine` (default: "auto") - "auto", "tesseract", "easyocr"

**OCRResponse:**
```json
{
  "text": "Extracted text content...",
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
  "request_id": "uuid"
}
```

## Analytics

| Method | Endpoint | Description | Auth | Query Params |
|--------|----------|-------------|------|--------------|
| GET | `/analytics/summary` | Analytics dashboard summary | JWT (admin/editor/viewer) | days |
| GET | `/analytics/queries` | Query statistics | JWT (admin/editor/viewer) | page, page_size |

**Query Parameters:**
- `days` (default: 7, max: 365) - Period to analyze

**AnalyticsSummary:**
```json
{
  "total_queries": 100,
  "total_feedback": 50,
  "avg_response_time_ms": 1234.5,
  "avg_rating": 4.2,
  "languages": {"en": 60, "hi": 40},
  "top_queries": [
    {
      "query": "Ministry of Culture",
      "count": 15,
      "avg_response_time_ms": 1200.0,
      "success_rate": 0.95,
      "most_common_language": "en"
    }
  ],
  "period_start": "2026-02-17T10:30:00Z",
  "period_end": "2026-02-24T10:30:00Z",
  "request_id": "uuid",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

## Admin (System Configuration)

| Method | Endpoint | Description | Auth | Body Schema |
|--------|----------|-------------|------|------------|
| POST | `/admin/login` | Admin login (returns JWT) | None | email, password |
| GET | `/admin/config` | Get system configuration | JWT (admin) | — |
| POST | `/admin/scrape/trigger` | Trigger web scraping job | JWT (admin) | target_urls, force_rescrape |
| GET | `/admin/scrape/status` | Get scraping job status | JWT (admin) | job_id |

**Login Request:**
```json
{
  "email": "admin@example.com",
  "password": "secure_password"
}
```

**Login Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Scrape Trigger:**
```json
{
  "target_urls": ["https://culture.gov.in", "https://asi.nic.in"],
  "force_rescrape": false
}
```

**Scrape Response:**
```json
{
  "job_id": "uuid",
  "status": "started|running|completed|failed",
  "target_count": 2,
  "started_at": "2026-02-24T10:30:00Z",
  "request_id": "uuid"
}
```

## Response Headers (All Endpoints)

| Header | Value | Description |
|--------|-------|-------------|
| `X-Request-ID` | UUID | Request tracking ID |
| `Content-Type` | application/json | JSON response |
| `Cache-Control` | Public/Private | Caching directive |

## Error Response (All Endpoints)

Status codes: 400, 401, 403, 404, 429, 500, 502, 503, 504

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {},
    "request_id": "uuid"
  }
}
```

## Authentication

### JWT Token (Header)
```
Authorization: Bearer <jwt_token>
```

### API Key (Header)
```
X-API-Key: key_<random>
```

## Rate Limits (per minute)

| Role | Limit |
|------|-------|
| admin | 120 |
| editor | 90 |
| viewer | 30 |
| api_consumer | 60 |

Response when exceeded:
```
HTTP 429 Too Many Requests
X-RateLimit-Remaining: 0
Retry-After: 60
```

## Supported Languages (ISO 639-1)

hi, en, bn, te, mr, ta, ur, gu, kn, ml, or, pa, as, mai, sa, ne, sd, kok, doi, mni, sat, bo, ks

---

**Last Updated**: 2026-02-24
**API Version**: 1.0.0
