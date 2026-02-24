# Shared Contracts & Cross-Agent Standards

**MANDATORY READING for ALL agents.** This file defines the shared contracts, naming conventions, data formats, and inter-service API schemas that every stream must follow to ensure consistency across the system.

**DEPLOYMENT TARGET: AWS VPC** — All services deploy inside a VPC on Amazon ECS. Managed services: RDS PostgreSQL, ElastiCache Redis, S3 (not S3). APIs are internal to VPC only; web frontends are public via ALB. Authentication is disabled (VPC isolation provides security).

---

## 1. Service Registry

**AWS Deployment:** Services communicate via AWS Cloud Map service discovery (`ragqa.local` private DNS namespace). Each service is reachable by `{service-name}.ragqa.local`.

**Local Development:** Services communicate over Docker network `rag-network` using Docker Compose service names.

| Service | Cloud Map Name / Docker Name | Internal Port | Service Discovery URL | Public Route (via ALB) |
|---|---|---|---|---|
| API Gateway | `api-gateway` | 8000 | `http://api-gateway.ragqa.local:8000` | `/api/*` (VPC-only via Internal ALB) |
| RAG Service | `rag-service` | 8001 | `http://rag-service.ragqa.local:8001` | — (internal only) |
| LLM Service | `llm-service` | 8002 | `http://llm-service.ragqa.local:8002` | — (internal only) |
| Speech Service | `speech-service` | 8003 | `http://speech-service.ragqa.local:8003` | — (internal only) |
| Translation Service | `translation-service` | 8004 | `http://translation-service.ragqa.local:8004` | — (internal only) |
| OCR Service | `ocr-service` | 8005 | `http://ocr-service.ragqa.local:8005` | — (internal only) |
| Data Ingestion | `data-ingestion` | 8006 | `http://data-ingestion.ragqa.local:8006` | — (internal only) |
| Model Training | `model-training` | 8007 | `http://model-training.ragqa.local:8007` | — (internal only) |
| Chat Widget (SPA) | `chat-widget` | 80 | `http://chat-widget.ragqa.local:80` | `/chat-widget/*` (Public ALB) |
| Search Page (SPA) | `search-page` | 80 | `http://search-page.ragqa.local:80` | `/search/*` (Public ALB) |
| Admin Dashboard (SPA) | `admin-dashboard` | 80 | `http://admin-dashboard.ragqa.local:80` | `/admin/*` (Public ALB) |
| PostgreSQL | — (AWS RDS) | 5432 | RDS endpoint from Terraform output | — |
| Redis | — (AWS ElastiCache) | 6379 | ElastiCache endpoint from Terraform output | — |
| Milvus | `milvus` | 19530 | `http://milvus.ragqa.local:19530` | — |
| Object Storage | — (AWS S3) | — | `s3://ragqa-documents`, `s3://ragqa-models`, `s3://ragqa-backups` | — |
| Prometheus | `prometheus` | 9090 | `http://prometheus.ragqa.local:9090` | — |
| Grafana | `grafana` | 3000 | `http://grafana.ragqa.local:3000` | `/grafana` (Public ALB) |
| Langfuse | `langfuse` | 3001 | `http://langfuse.ragqa.local:3001` | `/langfuse` (Public ALB) |
| Langfuse PostgreSQL | — (AWS RDS) | 5432 | RDS Langfuse endpoint from Terraform output | — |

---

## 2. AWS Infrastructure & Storage

### 2.1 VPC Layout

| Subnet | CIDR | AZ | Purpose |
|---|---|---|---|
| Public Subnet A | 10.0.1.0/24 | ap-south-1a | ALB, NAT Gateway |
| Public Subnet B | 10.0.2.0/24 | ap-south-1b | ALB (Multi-AZ) |
| Private Subnet A | 10.0.10.0/24 | ap-south-1a | All ECS services, RDS, ElastiCache |
| Private Subnet B | 10.0.11.0/24 | ap-south-1b | Multi-AZ replicas |

- **Internet access for scraping:** Private subnets route outbound traffic through NAT Gateway
- **Public web access:** ALB in public subnets forwards to frontend ECS services

### 2.2 AWS Managed Services (replace self-hosted)

| Component | AWS Service | Replaces |
|---|---|---|
| PostgreSQL | RDS PostgreSQL 16 (db.r6g.large, Multi-AZ) | Self-hosted PostgreSQL container |
| Langfuse DB | RDS PostgreSQL 16 (db.t4g.medium) | langfuse-postgres container |
| Redis | ElastiCache Redis 7.x (cache.r6g.large) | Self-hosted Redis container |
| Object Storage | S3 (3 buckets) | S3 |
| Container Registry | ECR (13 repositories) | — |
| Load Balancer | ALB (public + internal) | NGINX |
| DNS Discovery | Cloud Map (ragqa.local) | Docker network DNS |
| Logs | CloudWatch Logs | Loki |
| Secrets | Secrets Manager | .env file |

### 2.3 S3 Buckets (replace S3)

| Bucket | Purpose |
|---|---|
| `ragqa-documents` | Raw scraped documents, processed text, thumbnails, images |
| `ragqa-models` | Base model weights, fine-tuned LoRA adapters, training/eval data |
| `ragqa-backups` | RDS snapshots, Milvus snapshots, configuration backups |

### 2.4 ECS Compute

| Service Category | Compute | Instance Type |
|---|---|---|
| Frontends, API Gateway, OCR, Data Ingestion, Monitoring | ECS Fargate | Serverless |
| LLM, Speech, Translation, Model Training | ECS on EC2 | g5.2xlarge (NVIDIA A10G GPU) |
| Milvus | ECS Fargate + EFS | Serverless with persistent storage |

### 2.5 Local Development (Docker Compose)

For local development, `docker-compose.yml` uses local containers for PostgreSQL, Redis, and S3. The application code is designed to work with both local and AWS deployments via environment variables.

---

## 3. Environment Variables

All services read configuration from environment variables. The master `.env` file at project root defines all values. Services access only the variables they need.

### 3.1 Naming Convention

- Prefix with service scope: `POSTGRES_`, `REDIS_`, `MILVUS_`, `AWS_S3_`, `LLM_`, `RAG_`, `SPEECH_`, `TRANSLATION_`, `OCR_`, `INGESTION_`, `APP_`, `JWT_`, `LANGFUSE_`
- Use UPPER_SNAKE_CASE
- Boolean values: `true` / `false` (lowercase strings)
- Duration values: integer seconds (e.g., `SESSION_IDLE_TIMEOUT_SECONDS=1800`)

### 3.2 Complete Variable List

```bash
# ===== APPLICATION =====
APP_ENV=production                          # production | staging | development
APP_DEBUG=false
APP_LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR
APP_SECRET_KEY=<random-256-bit-hex>         # Used for encryption at rest

# ===== POSTGRES (main — AWS RDS) =====
POSTGRES_HOST=<rds-endpoint>.ap-south-1.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=ragqa
POSTGRES_USER=ragqa_user
POSTGRES_PASSWORD=<from-secrets-manager>
POSTGRES_SSL_MODE=require                   # RDS requires SSL

# ===== POSTGRES (Langfuse — AWS RDS) =====
LANGFUSE_PG_HOST=<rds-langfuse-endpoint>.ap-south-1.rds.amazonaws.com
LANGFUSE_PG_PORT=5432
LANGFUSE_PG_DB=langfuse
LANGFUSE_PG_USER=langfuse_user
LANGFUSE_PG_PASSWORD=<from-secrets-manager>

# ===== REDIS (AWS ElastiCache) =====
REDIS_HOST=<elasticache-endpoint>.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=<from-secrets-manager>
REDIS_SSL=true                              # ElastiCache in-transit encryption
REDIS_DB_CACHE=0                            # Query result cache
REDIS_DB_RATE_LIMIT=1                       # Rate limiter
REDIS_DB_SESSION=2                          # Session store
REDIS_DB_TRANSLATION=3                      # Translation cache

# ===== MILVUS =====
MILVUS_HOST=milvus.ragqa.local
MILVUS_PORT=19530
MILVUS_COLLECTION_TEXT=ministry_text         # Text embeddings collection
MILVUS_COLLECTION_IMAGE=ministry_images      # SigLIP image embeddings collection

# ===== AWS S3 (replaces S3) =====
AWS_DEFAULT_REGION=ap-south-1
AWS_S3_BUCKET_DOCUMENTS=ragqa-documents      # Raw ingested documents
AWS_S3_BUCKET_MODELS=ragqa-models            # Fine-tuned model weights
AWS_S3_BUCKET_BACKUPS=ragqa-backups          # Backup archives
# NOTE: No access keys needed — IAM roles provide credentials via instance metadata

# ===== AUTH =====
AUTH_ENABLED=false                           # Disabled — VPC network isolation provides security
JWT_SECRET_KEY=<secure-256-bit>              # Only used if AUTH_ENABLED=true
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== LLM SERVICE =====
LLM_SERVICE_URL=http://llm-service.ragqa.local:8002
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq
LLM_GPU_MEMORY_UTILIZATION=0.85
LLM_MAX_MODEL_LEN_STANDARD=8192
LLM_MAX_MODEL_LEN_LONGCTX=131072
LLM_MAX_MODEL_LEN_MULTIMODAL=8192

# ===== RAG SERVICE =====
RAG_SERVICE_URL=http://rag-service.ragqa.local:8001
RAG_EMBEDDING_MODEL=BAAI/bge-m3
RAG_VISION_EMBEDDING_MODEL=google/siglip-so400m-patch14-384
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_K=5
RAG_CONFIDENCE_THRESHOLD=0.65               # Below this → chatbot fallback
RAG_CACHE_TTL_SECONDS=3600                  # 1 hour default

# ===== SPEECH SERVICE =====
SPEECH_SERVICE_URL=http://speech-service.ragqa.local:8003
SPEECH_STT_MODEL=ai4bharat/indicconformer-hi-en
SPEECH_TTS_HINDI_MODEL=ai4bharat/indic-tts-hindi
SPEECH_TTS_ENGLISH_MODEL=coqui/tts-english
SPEECH_SAMPLE_RATE=16000

# ===== TRANSLATION SERVICE =====
TRANSLATION_SERVICE_URL=http://translation-service.ragqa.local:8004
TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B
TRANSLATION_CACHE_TTL_SECONDS=86400         # 24 hours

# ===== OCR SERVICE =====
OCR_SERVICE_URL=http://ocr-service.ragqa.local:8005
OCR_TESSERACT_LANG=hin+eng
OCR_EASYOCR_LANGS=hi,en

# ===== DATA INGESTION =====
INGESTION_SERVICE_URL=http://data-ingestion.ragqa.local:8006
INGESTION_SCRAPE_INTERVAL_HOURS=24
INGESTION_MAX_CONCURRENT_SPIDERS=4
INGESTION_RESPECT_ROBOTS_TXT=true

# ===== MODEL TRAINING =====
TRAINING_SERVICE_URL=http://model-training.ragqa.local:8007
TRAINING_LORA_RANK=16
TRAINING_LORA_ALPHA=32
TRAINING_LEARNING_RATE=2e-4
TRAINING_EPOCHS=3
TRAINING_BATCH_SIZE=4

# ===== LANGFUSE =====
LANGFUSE_HOST=http://langfuse.ragqa.local:3001
LANGFUSE_PUBLIC_KEY=<key>
LANGFUSE_SECRET_KEY=<key>

# ===== SESSION =====
SESSION_IDLE_TIMEOUT_SECONDS=1800           # 30 min
SESSION_MAX_TURNS=50                        # Max conversation turns before truncation
SESSION_CONTEXT_WINDOW_TOKENS=4096          # Max tokens to keep in context

# ===== DATA RETENTION (days) =====
RETENTION_CONVERSATIONS_DAYS=90
RETENTION_FEEDBACK_DAYS=365
RETENTION_AUDIT_LOG_DAYS=730                # 2 years
RETENTION_ANALYTICS_DAYS=365
RETENTION_TRANSLATION_CACHE_DAYS=30

# ===== RATE LIMITS (requests per minute, per role) =====
RATE_LIMIT_ADMIN=120
RATE_LIMIT_EDITOR=90
RATE_LIMIT_VIEWER=30
RATE_LIMIT_API_CONSUMER=60

# ===== ALB / TLS (replaces NGINX) =====
# TLS termination handled by AWS ALB with ACM certificate
ALB_DOMAIN=culture.gov.in
CORS_ALLOWED_ORIGINS=https://culture.gov.in,https://www.culture.gov.in

# ===== GPU (EC2 instances) =====
# GPU instances use g5.2xlarge with NVIDIA A10G
# NVIDIA drivers and CUDA are pre-installed via ECS-optimized GPU AMI
NVIDIA_DRIVER_MIN_VERSION=535
CUDA_MIN_VERSION=12.1
```

---

## 4. Standard Error Response Format

**All backend services** must return errors in this exact JSON structure:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Human-readable error description",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

### Standard Error Codes

| HTTP Status | Error Code | When |
|---|---|---|
| 400 | `INVALID_REQUEST` | Malformed request body or parameters |
| 400 | `INVALID_LANGUAGE` | Unsupported language code |
| 400 | `INVALID_AUDIO_FORMAT` | Unsupported audio format |
| 401 | `UNAUTHORIZED` | Missing or invalid auth token |
| 401 | `TOKEN_EXPIRED` | JWT has expired |
| 403 | `FORBIDDEN` | Valid auth but insufficient permissions |
| 403 | `API_KEY_REVOKED` | API key has been deactivated |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `DUPLICATE` | Duplicate content detected |
| 413 | `PAYLOAD_TOO_LARGE` | File or request body exceeds size limit |
| 422 | `PROCESSING_FAILED` | Service could process request but got bad result |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `UPSTREAM_ERROR` | Downstream service returned an error |
| 503 | `SERVICE_UNAVAILABLE` | Service is starting up or shutting down |
| 503 | `MODEL_LOADING` | LLM model is still loading into GPU memory |
| 504 | `UPSTREAM_TIMEOUT` | Downstream service timed out |

### Pydantic Model (Python services)

```python
from pydantic import BaseModel, Field
from typing import Optional, Any

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description")
    details: Optional[dict[str, Any]] = Field(default=None)
    request_id: Optional[str] = Field(default=None)

class ErrorResponse(BaseModel):
    error: ErrorDetail
```

### TypeScript Type (Frontend services)

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}
```

---

## 5. Standard Health Check Format

**Every service** must expose `GET /health` returning:

```json
{
  "status": "healthy",
  "service": "rag-service",
  "version": "1.0.0",
  "uptime_seconds": 3612,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "milvus": { "status": "healthy", "latency_ms": 12 },
    "redis": { "status": "healthy", "latency_ms": 2 }
  }
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `status` | `"healthy" \| "degraded" \| "unhealthy"` | yes | Overall service status |
| `service` | string | yes | Docker service name (matches Service Registry above) |
| `version` | string | yes | SemVer (read from `__version__` or `package.json`) |
| `uptime_seconds` | float | yes | Seconds since service started |
| `timestamp` | ISO 8601 UTC | yes | Current server time |
| `dependencies` | object | yes | Map of dependency name → `{status, latency_ms}` |

### Status logic

- `healthy`: all dependencies healthy
- `degraded`: some non-critical dependencies unhealthy (e.g., cache down but DB up)
- `unhealthy`: critical dependency down (return HTTP 503)

### Pydantic Model

```python
from pydantic import BaseModel
from datetime import datetime

class DependencyHealth(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: float

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: datetime
    dependencies: dict[str, DependencyHealth]
```

---

## 6. Standard Log Format

**All backend services** must use structured JSON logging with these fields:

```json
{
  "timestamp": "2026-02-24T10:30:00.123Z",
  "level": "INFO",
  "service": "api-gateway",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Chat query processed",
  "logger": "app.routers.chat",
  "extra": {
    "session_id": "abc123",
    "language": "hi",
    "latency_ms": 1234
  }
}
```

### Required Fields

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 UTC with milliseconds |
| `level` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `service` | Docker service name |
| `request_id` | UUID v4 from `X-Request-ID` header (propagated across services) |
| `message` | Human-readable log message |
| `logger` | Python module path (e.g., `app.services.retriever`) |

### PII Rules

- **NEVER** log: Aadhaar numbers, phone numbers, email addresses, user names, full query text containing PII
- **DO** log: session_id, user_id (UUID), language code, model_id, latency, status codes
- Use the `sanitizer` from `rag_shared.security.sanitizer` before logging any user-provided text

### Implementation

All Python services must use `rag_shared.middleware.logging.setup_json_logging(service_name)` from Stream 10 shared lib. This configures `structlog` with the required format.

---

## 7. Request ID Propagation

Every request entering via the API Gateway gets a UUID v4 `X-Request-ID` header. This header must be:

1. **Generated** by API Gateway if not present in incoming request
2. **Propagated** in all downstream HTTP calls between services
3. **Included** in all log entries (see §6)
4. **Returned** to the client in response headers

All service-to-service HTTP clients (in `rag_shared.clients.base_client`) must automatically forward `X-Request-ID`.

---

## 8. Inter-Service API Contracts

These are the exact request/response schemas for calls **between** backend services. The API Gateway orchestrates all inter-service calls.

### 8.1 API Gateway → RAG Service

**POST** `http://rag-service:8001/query` (for chatbot)

```json
// Request
{
  "query": "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
  "language": "hi",
  "session_id": "uuid",
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "top_k": 10,
  "rerank_top_k": 5,
  "filters": {
    "source_sites": [],
    "content_type": null,
    "date_from": null,
    "date_to": null
  }
}

// Response
{
  "context": "Assembled context text from retrieved chunks...",
  "sources": [
    {
      "title": "Document title",
      "url": "https://culture.gov.in/...",
      "snippet": "Relevant text snippet...",
      "score": 0.87,
      "source_site": "culture.gov.in",
      "language": "hi",
      "content_type": "webpage",
      "chunk_id": "milvus-id-123"
    }
  ],
  "confidence": 0.82,
  "cached": false
}
```

**POST** `http://rag-service:8001/search` (for search page)

```json
// Request
{
  "query": "Indian heritage sites",
  "language": "en",
  "page": 1,
  "page_size": 20,
  "filters": {
    "source_sites": ["asi.nic.in"],
    "content_type": "webpage",
    "date_from": "2024-01-01",
    "date_to": null,
    "language": null
  }
}

// Response
{
  "results": [
    {
      "title": "Protected Monuments",
      "url": "https://asi.nic.in/monuments",
      "snippet": "AI-generated snippet...",
      "score": 0.91,
      "source_site": "asi.nic.in",
      "language": "en",
      "content_type": "webpage",
      "thumbnail_url": "https://s3/documents/thumb_123.jpg",
      "published_date": "2025-06-15"
    }
  ],
  "multimedia": [
    {
      "type": "image",
      "url": "https://asi.nic.in/images/monument.jpg",
      "alt_text": "Taj Mahal front view",
      "source_site": "asi.nic.in",
      "thumbnail_url": "..."
    }
  ],
  "events": [
    {
      "title": "National Culture Festival 2026",
      "date": "2026-03-15",
      "venue": "New Delhi",
      "description": "Annual celebration...",
      "source_url": "https://culture.gov.in/events/...",
      "language": "en"
    }
  ],
  "total_results": 142,
  "page": 1,
  "page_size": 20,
  "cached": false
}
```

**POST** `http://rag-service:8001/ingest` (called by data-ingestion)

```json
// Request
{
  "document_id": "uuid",
  "title": "Document Title",
  "source_url": "https://...",
  "source_site": "culture.gov.in",
  "content": "Full text content...",
  "content_type": "webpage",
  "language": "hi",
  "metadata": {
    "author": "...",
    "published_date": "2025-01-15",
    "tags": ["heritage", "monuments"]
  },
  "images": [
    {
      "url": "https://...",
      "alt_text": "...",
      "s3_path": "documents/img_123.jpg"
    }
  ]
}

// Response
{
  "document_id": "uuid",
  "chunk_count": 12,
  "embedding_status": "completed",
  "milvus_ids": ["id1", "id2", "..."]
}
```

### 8.2 API Gateway → LLM Service

**POST** `http://llm-service:8002/v1/chat/completions` (OpenAI-compatible)

```json
// Request
{
  "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant..."},
    {"role": "user", "content": "Context: ...\n\nQuestion: ..."}
  ],
  "temperature": 0.3,
  "max_tokens": 1024,
  "stream": true,
  "model_version": "v1.2-finetuned"
}

// Response (non-streaming)
{
  "id": "chatcmpl-uuid",
  "model": "meta-llama/Llama-3.1-8B-Instruct-AWQ",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "Response text..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 512,
    "completion_tokens": 256,
    "total_tokens": 768
  }
}

// Response (streaming) — SSE format
data: {"id":"chatcmpl-uuid","choices":[{"delta":{"content":"token"},"index":0}]}
data: [DONE]
```

### 8.3 API Gateway → Speech Service

**POST** `http://speech-service:8003/stt`

```
Content-Type: multipart/form-data
Fields:
  - audio: binary file (WAV/MP3/WebM/OGG)
  - language: "hi" | "en" | "auto" (optional, default "auto")
```

```json
// Response
{
  "text": "Transcribed text here",
  "language": "hi",
  "confidence": 0.94,
  "duration_seconds": 3.5
}
```

**POST** `http://speech-service:8003/tts`

```json
// Request
{
  "text": "बोलने के लिए पाठ",
  "language": "hi",
  "format": "mp3",
  "voice": "default"
}

// Response
Content-Type: audio/mpeg
Body: binary audio data
Headers:
  X-Duration-Seconds: 2.3
  X-Language: hi
```

### 8.4 API Gateway → Translation Service

**POST** `http://translation-service:8004/translate`

```json
// Request
{
  "text": "Ministry of Culture promotes Indian heritage",
  "source_language": "en",
  "target_language": "hi"
}

// Response
{
  "translated_text": "संस्कृति मंत्रालय भारतीय विरासत को बढ़ावा देता है",
  "source_language": "en",
  "target_language": "hi",
  "cached": true
}
```

**POST** `http://translation-service:8004/translate/batch`

```json
// Request
{
  "texts": ["text1", "text2", "text3"],
  "source_language": "en",
  "target_language": "hi"
}

// Response
{
  "translations": [
    {"text": "translated1", "cached": false},
    {"text": "translated2", "cached": true},
    {"text": "translated3", "cached": false}
  ],
  "source_language": "en",
  "target_language": "hi"
}
```

**POST** `http://translation-service:8004/detect`

```json
// Request
{ "text": "यह हिंदी में लिखा गया है" }

// Response
{
  "language": "hi",
  "confidence": 0.97,
  "script": "Devanagari"
}
```

### 8.5 API Gateway → OCR Service

**POST** `http://ocr-service:8005/ocr`

```
Content-Type: multipart/form-data
Fields:
  - file: binary (PNG/JPG/PDF)
  - languages: "hi,en" (comma-separated)
  - engine: "auto" | "tesseract" | "easyocr" (optional, default "auto")
```

```json
// Response
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
  "confidence": 0.87
}
```

### 8.6 API Gateway → Data Ingestion

**POST** `http://data-ingestion:8006/jobs/trigger`

```json
// Request
{
  "target_urls": ["https://culture.gov.in"],
  "spider_type": "auto",
  "force_rescrape": false
}

// Response
{
  "job_id": "uuid",
  "status": "started",
  "target_count": 1,
  "started_at": "2026-02-24T10:30:00Z"
}
```

**GET** `http://data-ingestion:8006/jobs/status?job_id=uuid`

```json
{
  "job_id": "uuid",
  "status": "running",
  "progress": {
    "pages_crawled": 45,
    "pages_total": 120,
    "documents_ingested": 30,
    "errors": 2
  },
  "started_at": "2026-02-24T10:30:00Z",
  "elapsed_seconds": 180
}
```

### 8.7 API Gateway → Model Training

**POST** `http://model-training:8007/finetune/start`

```json
// Request
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

// Response
{
  "job_id": "uuid",
  "status": "started",
  "estimated_duration_minutes": 120
}
```

**POST** `http://model-training:8007/evaluate`

```json
// Request
{
  "model_version": "v1.2-finetuned",
  "eval_dataset": "s3://models/eval_data/hindi_qa_bench.jsonl",
  "metrics": ["exact_match", "f1", "bleu", "ndcg", "hallucination_rate"]
}

// Response
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

## 9. Language Codes

Use ISO 639-1 two-letter codes consistently. The `Language` enum in `rag_shared.models.language` is the single source of truth.

| Code | Language | Script |
|---|---|---|
| `hi` | Hindi | Devanagari |
| `en` | English | Latin |
| `bn` | Bengali | Bengali |
| `te` | Telugu | Telugu |
| `mr` | Marathi | Devanagari |
| `ta` | Tamil | Tamil |
| `ur` | Urdu | Perso-Arabic |
| `gu` | Gujarati | Gujarati |
| `kn` | Kannada | Kannada |
| `ml` | Malayalam | Malayalam |
| `or` | Odia | Odia |
| `pa` | Punjabi | Gurmukhi |
| `as` | Assamese | Bengali |
| `mai` | Maithili | Devanagari |
| `sa` | Sanskrit | Devanagari |
| `ne` | Nepali | Devanagari |
| `sd` | Sindhi | Perso-Arabic |
| `kok` | Konkani | Devanagari |
| `doi` | Dogri | Devanagari |
| `mni` | Manipuri | Meitei |
| `sat` | Santali | Ol Chiki |
| `bo` | Bodo | Devanagari |
| `ks` | Kashmiri | Perso-Arabic |

---

## 10. Pydantic & TypeScript Model Conventions

### Python (all backend services)

- **Field naming:** `snake_case` (e.g., `source_url`, `created_at`, `session_id`)
- **Timestamps:** `datetime` objects, serialized as ISO 8601 UTC (`"2026-02-24T10:30:00Z"`)
- **UUIDs:** `uuid.UUID` type, serialized as strings
- **Language fields:** use `str` validated against the Language enum
- **Pagination:** `page` (1-indexed), `page_size` (default 20, max 100)
- **IDs:** UUID v4 strings for all entity IDs
- **Pydantic config:** Use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility

### TypeScript (all frontend services)

- **Field naming:** `snake_case` (match API responses — no camelCase conversion)
- **API client:** use `fetch` with typed response interfaces
- **Timestamps:** ISO 8601 strings (display via `Intl.DateTimeFormat`)

### Shared Pagination

```python
# Python
class PaginatedRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
```

```typescript
// TypeScript
interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: T[];
}
```

---

## 11. Prometheus Metrics Convention

All Python services expose metrics at `GET /metrics` in Prometheus format.

### Required metrics per service

| Metric | Type | Labels | Description |
|---|---|---|---|
| `http_requests_total` | counter | `method`, `endpoint`, `status_code` | Total HTTP requests |
| `http_request_duration_seconds` | histogram | `method`, `endpoint` | Request latency |
| `http_request_size_bytes` | histogram | `method`, `endpoint` | Request body size |
| `http_response_size_bytes` | histogram | `method`, `endpoint` | Response body size |

### Service-specific metrics

- **LLM:** `llm_tokens_generated_total`, `llm_inference_duration_seconds`, `llm_model_loaded` (gauge, per model)
- **RAG:** `rag_retrieval_duration_seconds`, `rag_cache_hit_total`, `rag_cache_miss_total`
- **Speech:** `speech_stt_duration_seconds`, `speech_tts_duration_seconds`
- **Translation:** `translation_duration_seconds`, `translation_cache_hit_total`
- **Ingestion:** `ingestion_pages_crawled_total`, `ingestion_documents_ingested_total`, `ingestion_errors_total`

Use `rag_shared.middleware.metrics` for automatic HTTP metrics instrumentation.

---

## 12. RBAC Role Definitions

| Role | Scope | Allowed API Endpoints |
|---|---|---|
| `admin` | Full access | All endpoints including `/admin/*`, `/finetune/*`, config changes |
| `editor` | Content management | `/documents/*`, `/jobs/*`, `/analytics/*` (read), `/feedback` (read) |
| `viewer` | Read-only analytics | `/analytics/*` (read), `/conversations` (read), `/feedback` (read) |
| `api_consumer` | Widget/API access | `/chat`, `/chat/stream`, `/search`, `/search/suggest`, `/voice/*`, `/translate`, `/feedback` (write), `/ocr/upload` |

The API Gateway RBAC middleware reads the role from the JWT `role` claim and checks against the `permissions` table (resource + action).

---

## 13. Chatbot Fallback Behavior

When RAG retrieval `confidence < RAG_CONFIDENCE_THRESHOLD` (default 0.65) OR guardrails flag the response:

**Hindi fallback:**
```
मुझे इस विषय पर पर्याप्त जानकारी नहीं मिली। कृपया संस्कृति मंत्रालय हेल्पलाइन 011-23388261 पर संपर्क करें या arit-culture@gov.in पर ईमेल करें।
```

**English fallback:**
```
I'm unable to find a reliable answer to your question. Please contact the Ministry of Culture helpline at 011-23388261 or email arit-culture@gov.in.
```

---

## 14. Python Dependency Versions (pinned)

All Python services must use these versions for shared dependencies:

```
python==3.11.*
fastapi==0.115.*
uvicorn[standard]==0.34.*
pydantic==2.10.*
pydantic-settings==2.7.*
httpx==0.28.*
structlog==24.4.*
prometheus-client==0.21.*
redis==5.2.*
asyncpg==0.30.*
sqlalchemy[asyncio]==2.0.*
pymilvus==2.4.*
boto3==1.35.*
langfuse==2.56.*
python-multipart==0.0.18
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
```

Service-specific dependencies (not shared) can be pinned independently in each service's `requirements.txt`.

---

## 15. Frontend Shared Standards

### Common dependencies (all three frontends)

```json
{
  "react": "^18.3.0",
  "react-dom": "^18.3.0",
  "typescript": "^5.6.0",
  "vite": "^6.0.0",
  "i18next": "^24.0.0",
  "react-i18next": "^15.0.0"
}
```

### Additional (Chat Widget + Search Page)
```json
{
  "react-markdown": "^9.0.0",
  "eventsource-parser": "^3.0.0"
}
```

### Additional (Admin Dashboard)
```json
{
  "recharts": "^2.13.0",
  "react-router-dom": "^7.0.0",
  "@tanstack/react-table": "^8.20.0"
}
```

### API Base URL configuration

All frontends read the API base URL from a runtime environment variable injected at build time:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
```

### Shared TypeScript interfaces

Frontend streams 8, 9, and 11 must define TypeScript interfaces matching the JSON schemas in §8 above. The field names must be identical (`snake_case`).

---

## 16. S3 Bucket Structure (replaces S3)

All object storage uses AWS S3. Services access S3 via `boto3` with IAM role credentials (no access keys).

```
s3://ragqa-documents/
├── raw/                    # Raw scraped HTML/PDF/DOCX files
│   └── {source_site}/{document_id}.{ext}
├── processed/              # Extracted text after parsing
│   └── {document_id}.txt
├── thumbnails/             # Generated thumbnails for multimedia results
│   └── {document_id}_thumb.jpg
└── images/                 # Extracted images from documents/websites
    └── {document_id}/{image_id}.{ext}

s3://ragqa-models/
├── base/                   # Base model weights (downloaded once)
│   ├── llama-3.1-8b-instruct-awq/
│   ├── mistral-nemo-instruct-awq/
│   └── gemma-3-12b-it-awq/
├── finetuned/              # Fine-tuned LoRA adapters + merged models
│   └── {model_id}/{version}/
├── training_data/          # Prepared training datasets
│   └── {dataset_name}.jsonl
└── eval_data/              # Evaluation benchmark datasets
    └── {benchmark_name}.jsonl

s3://ragqa-backups/
├── rds-snapshots/          # RDS automated snapshots (managed by AWS)
├── milvus/                 # Milvus EFS snapshots
│   └── {date}/
└── config/                 # Configuration backups
    └── {date}/
```

**S3 Lifecycle Policies:**
- Standard → Infrequent Access after 90 days
- Infrequent Access → Glacier after 365 days
- Versioning enabled on all buckets
- Server-side encryption (AES-256)

---

## 17. Docker Compose Service Labels

All services must include these labels in `docker-compose.yml`:

```yaml
labels:
  - "com.ragqa.service=<service-name>"
  - "com.ragqa.version=1.0.0"
  - "com.ragqa.stream=<stream-number>"
```

---

## 18. GIGW Compliance Elements (Streams 8, 11)

Both the Chat Widget and Search Page must include:

1. **Government of India Emblem** (National Emblem) — prominently displayed
2. **Header:** "Ministry of Culture, Government of India" in both Hindi and English
3. **Language toggle:** Prominently placed Hindi ↔ English switch
4. **Footer** (mandatory text):
   - "Website Content Managed by Ministry of Culture"
   - "Designed, Developed and Hosted by NIC"
   - Last Updated: `{date}`
5. **Footer links:** Sitemap, Feedback, Terms & Conditions, Privacy Policy, Copyright Policy, Hyperlinking Policy, Accessibility Statement
6. **Skip-to-content link** (hidden, activated by keyboard)
7. **ARIA landmarks:** `role="banner"`, `role="navigation"`, `role="main"`, `role="contentinfo"`
