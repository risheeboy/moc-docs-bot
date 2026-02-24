# API Reference — RAG-Based Hindi QA System

**Version:** 1.0.0
**Last Updated:** February 24, 2026
**Base URL:** `https://culture.gov.in/api/v1` (Production)

---

## Table of Contents

1. [Authentication](#authentication)
2. [System & Health](#system--health)
3. [Chat Endpoints](#chat-endpoints)
4. [Search Endpoints](#search-endpoints)
5. [Voice Endpoints](#voice-endpoints)
6. [Translation Endpoints](#translation-endpoints)
7. [OCR Endpoints](#ocr-endpoints)
8. [Feedback Endpoints](#feedback-endpoints)
9. [Document Management](#document-management)
10. [Admin Endpoints](#admin-endpoints)
11. [Error Handling](#error-handling)
12. [Rate Limiting](#rate-limiting)

---

## Authentication

### Overview

The API Gateway uses JWT (JSON Web Token) bearer authentication. All requests except health checks and login must include a valid JWT token in the `Authorization` header.

### Obtain Token: `/auth/login`

**Endpoint:** `POST /auth/login`

Authenticate with email and password to receive JWT tokens.

**Request:**
```json
{
  "email": "user@culture.gov.in",
  "password": "secure_password_here"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Usage:**
```bash
curl -X POST https://culture.gov.in/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@culture.gov.in",
    "password": "secure_password_here"
  }'
```

### Refresh Token: `/auth/refresh`

**Endpoint:** `POST /auth/refresh`

Obtain a new access token using a valid refresh token (does not require login again).

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Usage:**
```bash
curl -X POST https://culture.gov.in/api/v1/auth/refresh \
  -H "Authorization: Bearer $REFRESH_TOKEN"
```

### Token Rules

- **Access Token Lifetime:** 60 minutes
- **Refresh Token Lifetime:** 7 days
- **Revocation:** Log out by invalidating tokens in the database (not automatic)
- **Required Header:** `Authorization: Bearer <access_token>` (all protected endpoints)

---

## System & Health

### Health Check: `GET /health`

Check service health without authentication.

**Endpoint:** `GET /health`

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "uptime_seconds": 3612.5,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "postgres": {
      "status": "healthy",
      "latency_ms": 5
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2
    },
    "milvus": {
      "status": "healthy",
      "latency_ms": 12
    },
    "llm_service": {
      "status": "healthy",
      "latency_ms": 1200
    }
  }
}
```

**Status Definitions:**
- `healthy`: All critical dependencies operational
- `degraded`: Some non-critical dependencies down (e.g., cache unavailable)
- `unhealthy`: Critical dependency failure (returns HTTP 503)

**Usage:**
```bash
curl https://culture.gov.in/api/v1/health
```

---

## Chat Endpoints

### Single-Turn Chat: `POST /chat`

Send a query to the chatbot and receive an immediate response with source citations.

**Endpoint:** `POST /chat`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "query": "भारतीय संस्कृति मंत्रालय की स्थापना कब हुई?",
  "language": "hi",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chat_history": [
    {
      "role": "user",
      "content": "नमस्ते"
    },
    {
      "role": "assistant",
      "content": "नमस्ते! मैं संस्कृति मंत्रालय की सहायता के लिए यहाँ हूँ। आप मुझसे कुछ भी पूछ सकते हैं।"
    }
  ],
  "top_k": 10,
  "rerank_top_k": 5,
  "filters": {
    "source_sites": ["culture.gov.in"],
    "content_type": null,
    "date_from": null,
    "date_to": null
  }
}
```

**Response (200 OK):**
```json
{
  "response": "संस्कृति मंत्रालय की स्थापना 1947 में की गई थी। यह मंत्रालय भारत की समृद्ध सांस्कृतिक विरासत को संरक्षित और प्रचारित करता है।",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "sources": [
    {
      "title": "संस्कृति मंत्रालय - परिचय",
      "url": "https://culture.gov.in/about",
      "snippet": "संस्कृति मंत्रालय की स्थापना स्वतंत्रता के बाद 1947 में की गई थी।",
      "score": 0.94,
      "source_site": "culture.gov.in",
      "language": "hi",
      "content_type": "webpage",
      "chunk_id": "milvus-chunk-7834",
      "published_date": "2025-01-15T00:00:00Z"
    },
    {
      "title": "Ministry of Culture Overview",
      "url": "https://culture.gov.in/about-en",
      "snippet": "The Ministry of Culture was established in 1947 to preserve and promote Indian cultural heritage.",
      "score": 0.91,
      "source_site": "culture.gov.in",
      "language": "en",
      "content_type": "webpage",
      "chunk_id": "milvus-chunk-7835",
      "published_date": "2025-01-15T00:00:00Z"
    }
  ],
  "confidence": 0.89,
  "language": "hi",
  "cached": false,
  "latency_ms": 1250
}
```

**Field Descriptions:**

| Field | Type | Description |
|---|---|---|
| `response` | string | Generated chatbot answer |
| `session_id` | uuid | Conversation identifier (can be reused for multi-turn) |
| `sources` | array | Documents used as context (ranked by relevance) |
| `confidence` | float (0-1) | How confident the system is in the response |
| `cached` | boolean | True if result retrieved from cache (no recomputation) |
| `latency_ms` | integer | Total response time in milliseconds |

**Error Responses:**

- **400 Bad Request:** Malformed JSON or invalid language code
- **401 Unauthorized:** Missing or expired JWT token
- **429 Too Many Requests:** Rate limit exceeded for your role
- **503 Service Unavailable:** LLM model still loading or service down

**Usage Example:**
```bash
curl -X POST https://culture.gov.in/api/v1/chat \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
    "language": "hi"
  }'
```

---

### Streaming Chat: `POST /chat/stream`

Stream a chat response in real-time using Server-Sent Events (SSE).

**Endpoint:** `POST /chat/stream`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:** (Same as `/chat`)

**Response (200 OK):**
```
data: {"event":"token","data":"संस्कृति"}
data: {"event":"token","data":" मंत्रालय"}
data: {"event":"token","data":" की"}
...
data: {"event":"sources","data":[{"title":"...","url":"..."}]}
data: {"event":"complete","data":{"confidence":0.89,"cached":false}}
```

**Stream Events:**

| Event | Data | Purpose |
|---|---|---|
| `token` | string | LLM output token (stream response token-by-token) |
| `sources` | array | Retrieved documents (sent before completion) |
| `complete` | object | Final metadata (confidence, cached status) |
| `error` | object | Error message if processing fails |

**Usage Example (JavaScript):**
```javascript
const eventSource = new EventSource(
  'https://culture.gov.in/api/v1/chat/stream',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: 'भारतीय संस्कृति के बारे में बताइए',
      language: 'hi'
    })
  }
);

eventSource.onmessage = (event) => {
  const {event: type, data} = JSON.parse(event.data);
  if (type === 'token') {
    console.log(data);  // Append to UI in real-time
  } else if (type === 'sources') {
    updateSourcesList(JSON.parse(data));
  } else if (type === 'complete') {
    eventSource.close();
  }
};
```

---

### Get Conversation History: `GET /chat/sessions/{session_id}/history`

Retrieve full conversation history for a session.

**Endpoint:** `GET /chat/sessions/{session_id}/history`

**Path Parameters:**
```
session_id: UUID (required)
```

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-20T14:30:00Z",
  "updated_at": "2026-02-24T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "नमस्ते",
      "timestamp": "2026-02-20T14:30:15Z",
      "language": "hi"
    },
    {
      "role": "assistant",
      "content": "नमस्ते! संस्कृति मंत्रालय में आपका स्वागत है।",
      "timestamp": "2026-02-20T14:30:45Z",
      "language": "hi"
    },
    {
      "role": "user",
      "content": "आपकी स्थापना कब हुई?",
      "timestamp": "2026-02-20T14:31:00Z",
      "language": "hi"
    }
  ]
}
```

---

### Clear Conversation: `POST /chat/sessions/{session_id}/clear`

Delete all messages in a session. This action cannot be undone.

**Endpoint:** `POST /chat/sessions/{session_id}/clear`

**Path Parameters:**
```
session_id: UUID (required)
```

**Response (204 No Content):**
```
(empty body)
```

---

## Search Endpoints

### Unified Search: `POST /search`

Full-text and semantic search across all 30 Ministry platforms. Returns ranked results with AI-generated summaries and multimedia.

**Endpoint:** `POST /search`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "query": "Indian heritage sites monuments",
  "language": "en",
  "page": 1,
  "page_size": 20,
  "filters": {
    "source_sites": ["asi.nic.in", "culture.gov.in"],
    "content_type": "webpage",
    "date_from": "2024-01-01",
    "date_to": null,
    "language": null
  }
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "title": "Protected Monuments Database",
      "url": "https://asi.nic.in/monuments/protected",
      "snippet": "The Archaeological Survey of India maintains a comprehensive database of over 3,686 protected monuments across India. These sites represent millennia of cultural and architectural heritage spanning from prehistoric times to the medieval period.",
      "score": 0.96,
      "source_site": "asi.nic.in",
      "language": "en",
      "content_type": "webpage",
      "thumbnail_url": "https://culture.gov.in/thumbnails/asi-monuments.jpg",
      "published_date": "2025-06-15"
    },
    {
      "title": "Heritage Conservation Programs",
      "url": "https://culture.gov.in/conservation",
      "snippet": "The Ministry of Culture implements various programs to conserve and preserve India's heritage sites. This includes restoration projects, documentation, and community engagement initiatives.",
      "score": 0.91,
      "source_site": "culture.gov.in",
      "language": "en",
      "content_type": "webpage",
      "thumbnail_url": "https://culture.gov.in/thumbnails/conservation.jpg",
      "published_date": "2025-03-20"
    }
  ],
  "multimedia": [
    {
      "type": "image",
      "url": "https://asi.nic.in/images/taj-mahal.jpg",
      "alt_text": "Taj Mahal front view with gardens",
      "source_site": "asi.nic.in",
      "thumbnail_url": "https://culture.gov.in/thumbnails/taj-mahal-thumb.jpg"
    },
    {
      "type": "image",
      "url": "https://culture.gov.in/images/qutb-minar.jpg",
      "alt_text": "Qutb Minar monument in Delhi",
      "source_site": "culture.gov.in",
      "thumbnail_url": "https://culture.gov.in/thumbnails/qutb-thumb.jpg"
    }
  ],
  "events": [
    {
      "title": "National Culture Festival 2026",
      "date": "2026-03-15",
      "venue": "New Delhi Convention Centre",
      "description": "Annual celebration of Indian cultural diversity featuring performances, exhibitions, and workshops.",
      "source_url": "https://culture.gov.in/events/ncf-2026",
      "language": "en"
    }
  ],
  "total_results": 342,
  "page": 1,
  "page_size": 20,
  "cached": false
}
```

**Pagination:**
- Use `page` and `page_size` for pagination
- Maximum `page_size`: 100
- First page is `page=1` (not 0-indexed)

---

### Search Suggestions: `GET /search/suggest`

Get auto-complete suggestions based on query prefix.

**Endpoint:** `GET /search/suggest`

**Query Parameters:**
```
q=indus&language=en
```

**Response (200 OK):**
```json
{
  "suggestions": [
    "indus valley civilization",
    "indian art forms",
    "indus script",
    "indigenous crafts",
    "indian architecture"
  ]
}
```

---

## Voice Endpoints

### Speech-to-Text: `POST /voice/stt`

Convert audio input to text with automatic Hindi/English language detection.

**Endpoint:** `POST /voice/stt`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
```
POST /voice/stt HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="audio"; filename="query.wav"
Content-Type: audio/wav

[binary audio data]
------WebKitFormBoundary
Content-Disposition: form-data; name="language"

auto
------WebKitFormBoundary--
```

**Supported Formats:** WAV, MP3, WebM, OGG

**Response (200 OK):**
```json
{
  "text": "भारतीय संस्कृति के बारे में बताइए",
  "language": "hi",
  "confidence": 0.94,
  "duration_seconds": 3.5
}
```

**Usage Example (JavaScript):**
```javascript
const audioBlob = await recording.getBlob();
const formData = new FormData();
formData.append('audio', audioBlob, 'query.wav');
formData.append('language', 'auto');

const response = await fetch(
  'https://culture.gov.in/api/v1/voice/stt',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    body: formData
  }
);

const {text, language, confidence} = await response.json();
console.log(`Transcribed: "${text}" (${language}, confidence: ${confidence})`);
```

---

### Text-to-Speech: `POST /voice/tts`

Convert text to audio in Hindi or English.

**Endpoint:** `POST /voice/tts`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "text": "भारतीय संस्कृति मंत्रालय आपका स्वागत करता है",
  "language": "hi",
  "format": "mp3",
  "voice": "default"
}
```

**Response (200 OK):**
```
Content-Type: audio/mpeg
X-Duration-Seconds: 2.3
X-Language: hi

[binary audio data]
```

**Response Headers:**
- `X-Duration-Seconds`: Audio duration in seconds
- `X-Language`: Actual language of output

---

## Translation Endpoints

### Single Translation: `POST /translate`

Translate text between Hindi and English.

**Endpoint:** `POST /translate`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "text": "Ministry of Culture promotes Indian heritage",
  "source_language": "en",
  "target_language": "hi"
}
```

**Response (200 OK):**
```json
{
  "translated_text": "संस्कृति मंत्रालय भारतीय विरासत को बढ़ावा देता है",
  "source_language": "en",
  "target_language": "hi",
  "cached": false
}
```

**Caching:** Repeated translations are cached for 24 hours (indicated by `cached: true`).

---

### Batch Translation: `POST /translate/batch`

Translate multiple texts efficiently in a single request (up to 100 texts).

**Endpoint:** `POST /translate/batch`

**Request:**
```json
{
  "texts": [
    "Ministry of Culture",
    "Archaeological Survey of India",
    "Indian Heritage"
  ],
  "source_language": "en",
  "target_language": "hi"
}
```

**Response (200 OK):**
```json
{
  "translations": [
    {
      "text": "संस्कृति मंत्रालय",
      "cached": false
    },
    {
      "text": "भारतीय पुरातत्व सर्वेक्षण",
      "cached": true
    },
    {
      "text": "भारतीय विरासत",
      "cached": false
    }
  ],
  "source_language": "en",
  "target_language": "hi"
}
```

---

## OCR Endpoints

### OCR Upload: `POST /ocr/upload`

Extract text from images and PDFs in Hindi and English with confidence scores and bounding boxes.

**Endpoint:** `POST /ocr/upload`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
```
POST /ocr/upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[binary PDF data]
------WebKitFormBoundary
Content-Disposition: form-data; name="languages"

hi,en
------WebKitFormBoundary
Content-Disposition: form-data; name="engine"

auto
------WebKitFormBoundary--
```

**Parameters:**
- `file` (required): PNG, JPG, or PDF
- `languages` (default: "hi,en"): Comma-separated language codes
- `engine` (default: "auto"): "tesseract", "easyocr", or "auto"

**Response (200 OK):**
```json
{
  "text": "संस्कृति मंत्रालय\nMinistry of Culture\nभारत सरकार",
  "pages": [
    {
      "page_number": 1,
      "text": "संस्कृति मंत्रालय",
      "regions": [
        {
          "text": "संस्कृति मंत्रालय",
          "bounding_box": [50, 100, 300, 150],
          "confidence": 0.92,
          "type": "heading"
        },
        {
          "text": "Ministry of Culture",
          "bounding_box": [50, 160, 300, 200],
          "confidence": 0.89,
          "type": "text"
        }
      ]
    }
  ],
  "language": "hi",
  "engine_used": "easyocr",
  "confidence": 0.90
}
```

---

## Feedback Endpoints

### Submit Feedback: `POST /feedback`

Submit feedback on chat response quality, search results, or general experience.

**Endpoint:** `POST /feedback`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "550e8400-e29b-41d4-a716-446655440001",
  "rating": 4,
  "feedback_type": "accuracy",
  "comment": "Response was accurate but could include more details about 15th century architecture"
}
```

**Response (201 Created):**
```json
{
  "feedback_id": "550e8400-e29b-41d4-a716-446655440010"
}
```

**Rating Scale:** 1-5 (1=Poor, 5=Excellent)

**Feedback Types:**
- `accuracy`: Factual correctness
- `relevance`: How well response addresses the query
- `completeness`: Sufficient detail level
- `language_quality`: Grammar and clarity
- `other`: General feedback

---

## Document Management

### Upload Document: `POST /documents/upload`

Upload a document for ingestion into the RAG system.

**Endpoint:** `POST /documents/upload`

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request:**
```
POST /documents/upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="heritage-guide.pdf"
Content-Type: application/pdf

[binary PDF data]
------WebKitFormBoundary
Content-Disposition: form-data; name="title"

Indian Heritage Sites Guide 2026
------WebKitFormBoundary
Content-Disposition: form-data; name="language"

en
------WebKitFormBoundary--
```

**Response (202 Accepted):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440020",
  "status": "queued",
  "message": "Document queued for processing"
}
```

**Supported Formats:** PDF, DOCX, PPTX, PNG, JPG

---

### List Documents: `GET /documents`

List all ingested documents with filtering and pagination.

**Endpoint:** `GET /documents`

**Query Parameters:**
```
?page=1&page_size=20&source_site=culture.gov.in&content_type=webpage
```

**Response (200 OK):**
```json
{
  "total": 342,
  "page": 1,
  "page_size": 20,
  "total_pages": 18,
  "items": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440020",
      "title": "Heritage Conservation Report 2025",
      "source_url": "https://culture.gov.in/reports/conservation-2025",
      "source_site": "culture.gov.in",
      "content_type": "webpage",
      "language": "en",
      "created_at": "2025-12-15T10:30:00Z",
      "chunk_count": 34
    }
  ]
}
```

---

### Get Document Details: `GET /documents/{document_id}`

Retrieve full metadata and content for a document.

**Endpoint:** `GET /documents/{document_id}`

**Path Parameters:**
```
document_id: UUID (required)
```

**Response (200 OK):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440020",
  "title": "Heritage Conservation Report 2025",
  "source_url": "https://culture.gov.in/reports/conservation-2025",
  "source_site": "culture.gov.in",
  "content_type": "webpage",
  "language": "en",
  "created_at": "2025-12-15T10:30:00Z",
  "updated_at": "2026-02-20T14:30:00Z",
  "chunk_count": 34,
  "content": "Full text content of the document...",
  "metadata": {
    "author": "Ministry of Culture Research Team",
    "published_date": "2025-12-01",
    "tags": ["heritage", "conservation", "monuments"]
  },
  "images": [
    {
      "image_id": "img-001",
      "url": "https://culture.gov.in/images/heritage-1.jpg",
      "alt_text": "Taj Mahal restoration work",
      "minio_path": "documents/img-001.jpg"
    }
  ]
}
```

---

### Delete Document: `DELETE /documents/{document_id}`

Remove document from RAG system and vector database.

**Endpoint:** `DELETE /documents/{document_id}`

**Response (204 No Content):**
```
(empty body)
```

---

## Admin Endpoints

### Trigger Data Ingestion: `POST /admin/ingestion/jobs`

Start scraping and ingestion for specified Ministry websites.

**Endpoint:** `POST /admin/ingestion/jobs`

**Headers:**
```
Authorization: Bearer <access_token>
X-Role: admin|editor
```

**Request:**
```json
{
  "target_urls": [
    "https://culture.gov.in",
    "https://asi.nic.in",
    "https://sangeet-nrityam.gov.in"
  ],
  "spider_type": "auto",
  "force_rescrape": false
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440030",
  "status": "started",
  "target_count": 3,
  "started_at": "2026-02-24T10:30:00Z"
}
```

---

### Check Ingestion Status: `GET /admin/ingestion/jobs/{job_id}`

Get progress of a data ingestion job.

**Endpoint:** `GET /admin/ingestion/jobs/{job_id}`

**Response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440030",
  "status": "running",
  "progress": {
    "pages_crawled": 145,
    "pages_total": 500,
    "documents_ingested": 98,
    "errors": 2
  },
  "started_at": "2026-02-24T10:30:00Z",
  "elapsed_seconds": 1800
}
```

**Status Values:** `queued`, `running`, `completed`, `failed`

---

### Start Model Fine-Tuning: `POST /admin/models/finetune`

Fine-tune an LLM on Ministry QA dataset.

**Endpoint:** `POST /admin/models/finetune`

**Request:**
```json
{
  "base_model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "dataset_path": "s3://models/training_data/ministry_qa_v2.jsonl",
  "hyperparameters": {
    "lora_rank": 16,
    "lora_alpha": 32,
    "learning_rate": 0.0002,
    "epochs": 3,
    "batch_size": 4
  }
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440040",
  "status": "started",
  "estimated_duration_minutes": 120
}
```

---

### Evaluate Model: `POST /admin/models/evaluate`

Run evaluation metrics on a model using benchmark dataset.

**Endpoint:** `POST /admin/models/evaluate`

**Request:**
```json
{
  "model_version": "v1.2-finetuned",
  "eval_dataset": "s3://models/eval_data/hindi_qa_bench.jsonl",
  "metrics": ["exact_match", "f1", "bleu", "ndcg", "hallucination_rate"]
}
```

**Response (200 OK):**
```json
{
  "model_version": "v1.2-finetuned",
  "results": {
    "exact_match": 0.72,
    "f1": 0.84,
    "bleu": 0.45,
    "ndcg": 0.78,
    "hallucination_rate": 0.08,
    "llm_judge_score": 4.2
  },
  "eval_samples": 500,
  "evaluated_at": "2026-02-24T12:00:00Z"
}
```

---

### Conversation Analytics: `GET /admin/analytics/conversations`

Get metrics on conversation volume, duration, and languages.

**Endpoint:** `GET /admin/analytics/conversations`

**Query Parameters:**
```
?date_from=2026-02-01&date_to=2026-02-24
```

**Response (200 OK):**
```json
{
  "total_conversations": 12450,
  "total_turns": 45320,
  "average_turns_per_conversation": 3.64,
  "average_response_time_ms": 1250,
  "language_distribution": {
    "hi": 7850,
    "en": 4600
  },
  "top_queries": [
    {
      "query": "heritage sites near me",
      "count": 345
    },
    {
      "query": "भारतीय संस्कृति की जानकारी",
      "count": 298
    }
  ],
  "user_satisfaction": {
    "avg_rating": 4.2,
    "total_ratings": 3420
  }
}
```

---

### Audit Logs: `GET /admin/audit-logs`

Query system audit logs for compliance and troubleshooting.

**Endpoint:** `GET /admin/audit-logs`

**Query Parameters:**
```
?action=document_delete&user_id=user-123&date_from=2026-02-01&page=1
```

**Response (200 OK):**
```json
{
  "total": 245,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "timestamp": "2026-02-24T09:15:30Z",
      "action": "document_delete",
      "user_id": "user-123",
      "resource": "document-001",
      "details": {
        "title": "Old Heritage Report",
        "reason": "Outdated content"
      }
    }
  ]
}
```

---

## Error Handling

### Standard Error Response Format

All API errors follow this consistent JSON structure:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests for your role. Current limit: 30 per minute",
    "details": {
      "limit": 30,
      "window_seconds": 60,
      "retry_after_seconds": 45
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440099"
  }
}
```

### Error Codes Reference

| HTTP Status | Code | When |
|---|---|---|
| 400 | `INVALID_REQUEST` | Malformed JSON or missing required fields |
| 400 | `INVALID_LANGUAGE` | Language code not in {hi, en} |
| 400 | `INVALID_AUDIO_FORMAT` | Audio format not supported |
| 401 | `UNAUTHORIZED` | Missing or invalid JWT token |
| 401 | `TOKEN_EXPIRED` | JWT has expired (use refresh endpoint) |
| 403 | `FORBIDDEN` | Authenticated but insufficient permissions |
| 403 | `API_KEY_REVOKED` | API key has been deactivated |
| 404 | `NOT_FOUND` | Resource (session, document, etc.) not found |
| 409 | `DUPLICATE` | Duplicate content detected |
| 413 | `PAYLOAD_TOO_LARGE` | File or request body exceeds size limit |
| 422 | `PROCESSING_FAILED` | Service processed request but got bad result |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests (see rate limiting below) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `UPSTREAM_ERROR` | Downstream service returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Service is starting up or shutting down |
| 503 | `MODEL_LOADING` | LLM model is still loading into GPU memory |
| 504 | `UPSTREAM_TIMEOUT` | Downstream service timed out |

---

## Rate Limiting

### Per-Role Limits

Rate limits are applied per role per minute:

| Role | Requests/Minute |
|---|---|
| `admin` | 120 |
| `editor` | 90 |
| `viewer` | 30 |
| `api_consumer` (widget) | 60 |

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1645344060
```

### When Limit Exceeded

Returns **429 Too Many Requests** with retry info:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 30 requests per minute",
    "details": {
      "limit": 30,
      "window_seconds": 60,
      "retry_after_seconds": 45
    }
  }
}
```

### How to Handle Rate Limits

1. Check `X-RateLimit-Remaining` header
2. If approaching limit, implement exponential backoff
3. Use `Retry-After` header value for backoff timing
4. Cache results to reduce API calls

---

## Webhooks & Events (Future)

Webhook support for async operations is planned for v1.1:
- Ingestion job completion
- Model training completion
- System alerts

Subscribe via admin dashboard (not yet available).

---

## SDK Support

Official SDKs planned for:
- **Python:** `pip install rag-qa-sdk`
- **JavaScript/Node:** `npm install rag-qa-sdk`

See respective repositories for installation and usage.

---

## Support & Issues

For API issues or questions:
- **Email:** arit-culture@gov.in
- **Documentation:** https://culture.gov.in/docs/api
- **Status Page:** https://status.culture.gov.in

---

**Last Updated:** February 24, 2026
**API Version:** 1.0.0
