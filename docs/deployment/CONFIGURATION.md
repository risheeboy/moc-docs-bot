# Configuration Reference

**Version:** 1.0.0
**Source:** Shared Contracts §3.2
**Last Updated:** February 24, 2026

---

## Overview

All services are configured via environment variables defined in a master `.env` file at the project root. Each service reads only the variables it needs from this file.

**File Location:** `/path/to/rag-qa-hindi/.env`

---

## Environment Variables

### APPLICATION

```bash
# Environment: production | staging | development
APP_ENV=production

# Enable debug mode (disable in production)
APP_DEBUG=false

# Log level: DEBUG | INFO | WARNING | ERROR | CRITICAL
APP_LOG_LEVEL=INFO

# 256-bit hex key used for encryption at rest
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
APP_SECRET_KEY=<random-256-bit-hex>
```

**Notes:**
- `APP_ENV=production` enables enhanced security, disables debug endpoints
- `APP_DEBUG=false` required for RFP compliance
- `APP_LOG_LEVEL=INFO` recommended for production; use DEBUG only during troubleshooting

---

### PostgreSQL (Main Database)

```bash
# Database host (Docker service name for internal, or IP for external)
POSTGRES_HOST=postgres

# Database port
POSTGRES_PORT=5432

# Database name
POSTGRES_DB=ragqa

# Database user
POSTGRES_USER=ragqa_user

# Database password
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
POSTGRES_PASSWORD=<secure-password>
```

**Notes:**
- Password must be at least 32 characters
- Use same credentials in `docker-compose.yml` and `.env`
- Default port 5432 is standard for PostgreSQL

**Connection String (for reference):**
```
postgresql://ragqa_user:<password>@postgres:5432/ragqa
```

---

### PostgreSQL (Langfuse)

```bash
# Langfuse PostgreSQL host
LANGFUSE_PG_HOST=langfuse-postgres

# Langfuse PostgreSQL port
LANGFUSE_PG_PORT=5433

# Langfuse database name
LANGFUSE_PG_DB=langfuse

# Langfuse database user
LANGFUSE_PG_USER=langfuse_user

# Langfuse database password
LANGFUSE_PG_PASSWORD=<secure-password>
```

**Notes:**
- Langfuse uses separate PostgreSQL instance (port 5433)
- Critical for LLM observability and cost tracking

---

### Redis

```bash
# Redis host
REDIS_HOST=redis

# Redis port
REDIS_PORT=6379

# Redis password
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
REDIS_PASSWORD=<secure-password>

# Redis database 0: query result cache
REDIS_DB_CACHE=0

# Redis database 1: rate limiter
REDIS_DB_RATE_LIMIT=1

# Redis database 2: session store
REDIS_DB_SESSION=2

# Redis database 3: translation cache
REDIS_DB_TRANSLATION=3
```

**Notes:**
- Redis uses separate DB indices to isolate concerns
- Password must be set even if using localhost
- Default port is 6379

---

### Milvus (Vector Database)

```bash
# Milvus host
MILVUS_HOST=milvus

# Milvus port
MILVUS_PORT=19530

# Collection name for text embeddings
MILVUS_COLLECTION_TEXT=ministry_text

# Collection name for image embeddings (SigLIP)
MILVUS_COLLECTION_IMAGE=ministry_images
```

**Notes:**
- Milvus uses gRPC protocol (not HTTP)
- Collections are created automatically on first ingestion
- Embedding dimensions:
  - Text (BGE-M3): 1024 dimensions
  - Image (SigLIP): 768 dimensions

---

### S3 (Object Storage)

```bash
# S3 endpoint (without protocol)
MINIO_ENDPOINT=minio:9000

# S3 access key (username)
MINIO_ACCESS_KEY=<secure-key>

# S3 secret key (password)
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
MINIO_SECRET_KEY=<secure-password>

# S3 bucket for raw ingested documents
MINIO_BUCKET_DOCUMENTS=documents

# S3 bucket for fine-tuned model weights
MINIO_BUCKET_MODELS=models

# S3 bucket for backup archives
MINIO_BUCKET_BACKUPS=backups

# Use SSL/TLS for S3 (false for internal traffic; TLS at NGINX layer)
MINIO_USE_SSL=false
```

**Notes:**
- S3 provides S3-compatible object storage
- Access key should be at least 3 characters, secret 8+ characters
- Buckets are created automatically if not present
- `MINIO_USE_SSL=false` is safe for internal Docker network

**Bucket Structure Reference (see §16 of Shared Contracts):**
```
documents/
├── raw/
├── processed/
├── thumbnails/
└── images/

models/
├── base/
├── finetuned/
├── training_data/
└── eval_data/

backups/
├── postgres/
├── milvus/
├── redis/
└── minio/
```

---

### JWT (JSON Web Tokens)

```bash
# JWT secret key for token signing (256-bit hex)
# Generate: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<secure-256-bit>

# JWT signing algorithm
JWT_ALGORITHM=HS256

# Access token lifetime (minutes)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Refresh token lifetime (days)
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Notes:**
- Access tokens are short-lived (1 hour), require refresh
- Refresh tokens are longer-lived (7 days)
- Using HS256 (HMAC SHA-256) for symmetric signing
- Tokens are stateless (no server-side session store required)

---

### LLM Service

```bash
# LLM Service base URL
LLM_SERVICE_URL=http://llm-service:8002

# Standard LLM model (8B, fast inference)
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ

# Long-context LLM model (12B, 128K token window)
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ

# Multimodal LLM model (can process images)
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq

# GPU memory utilization ratio (0-1)
# Reduce if out-of-memory errors occur
LLM_GPU_MEMORY_UTILIZATION=0.85

# Maximum sequence length for standard model
LLM_MAX_MODEL_LEN_STANDARD=8192

# Maximum sequence length for long-context model
LLM_MAX_MODEL_LEN_LONGCTX=131072

# Maximum sequence length for multimodal model
LLM_MAX_MODEL_LEN_MULTIMODAL=8192
```

**Notes:**
- All models use AWQ quantization (4-bit) for efficiency
- LLM_GPU_MEMORY_UTILIZATION: balance between throughput and memory safety
  - 0.85 = aggressive (may cause OOM on heavy load)
  - 0.70 = conservative (safer but slower)
- Download and cache models on first startup (takes 10-15 minutes)

**Model Details:**
| Model | Params | Context | Speed | Use Case |
|---|---|---|---|---|
| Llama 3.1 8B | 8B | 8K | Fast | Default chatbot responses |
| Mistral NeMo 12B | 12B | 128K | Medium | Long documents, summaries |
| Gemma 3 12B | 12B | 8K | Medium | Image understanding, OCR |

---

### RAG Service

```bash
# RAG Service base URL
RAG_SERVICE_URL=http://rag-service:8001

# Text embedding model (multilingual, 1024 dims)
RAG_EMBEDDING_MODEL=BAAI/bge-m3

# Vision embedding model for image search (768 dims)
RAG_VISION_EMBEDDING_MODEL=google/siglip-so400m-patch14-384

# Chunk size for document splitting (tokens)
RAG_CHUNK_SIZE=512

# Overlap between chunks (to maintain context)
RAG_CHUNK_OVERLAP=64

# Number of top documents to retrieve (before reranking)
RAG_TOP_K=10

# Number of results after reranking
RAG_RERANK_TOP_K=5

# Confidence threshold below which chatbot falls back to helpline
RAG_CONFIDENCE_THRESHOLD=0.65

# Cache TTL for query results (seconds)
RAG_CACHE_TTL_SECONDS=3600
```

**Notes:**
- Chunk size 512 tokens ≈ 300-400 words
- Overlap prevents loss of context at chunk boundaries
- Reranking uses cross-encoder for better relevance
- Confidence below 0.65 triggers helpline fallback
- Cache TTL 3600s (1 hour) balances freshness vs. performance

---

### Speech Service

```bash
# Speech Service base URL
SPEECH_SERVICE_URL=http://speech-service:8003

# Speech-to-Text model (Hindi + English)
SPEECH_STT_MODEL=ai4bharat/indicconformer-hi-en

# Text-to-Speech Hindi model
SPEECH_TTS_HINDI_MODEL=ai4bharat/indic-tts-hindi

# Text-to-Speech English model
SPEECH_TTS_ENGLISH_MODEL=coqui/tts-english

# Audio sample rate (Hz)
SPEECH_SAMPLE_RATE=16000
```

**Notes:**
- IndicConformer achieves 95%+ accuracy for Hindi/English
- Sample rate 16kHz is standard for speech processing
- TTS models cached after first use
- Each model is ~500MB-1GB on disk

---

### Translation Service

```bash
# Translation Service base URL
TRANSLATION_SERVICE_URL=http://translation-service:8004

# Translation model (Hindi ↔ English)
TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B

# Translation cache TTL (seconds)
TRANSLATION_CACHE_TTL_SECONDS=86400
```

**Notes:**
- IndicTrans2 supports 22 Indian languages
- Cache TTL 86400s (24 hours)
- Model ~1GB on disk

---

### OCR Service

```bash
# OCR Service base URL
OCR_SERVICE_URL=http://ocr-service:8005

# Tesseract languages
OCR_TESSERACT_LANG=hin+eng

# EasyOCR languages
OCR_EASYOCR_LANGS=hi,en
```

**Notes:**
- Tesseract: fast, rule-based
- EasyOCR: slower, deep-learning based, more accurate
- Both run in parallel for best results

---

### Data Ingestion

```bash
# Data Ingestion Service base URL
INGESTION_SERVICE_URL=http://data-ingestion:8006

# Scraping interval (hours)
INGESTION_SCRAPE_INTERVAL_HOURS=24

# Maximum concurrent spiders
INGESTION_MAX_CONCURRENT_SPIDERS=4

# Respect robots.txt
INGESTION_RESPECT_ROBOTS_TXT=true
```

**Notes:**
- Scrapy crawls every 24 hours by default
- Max 4 concurrent spiders balances resource usage
- Always respect robots.txt for ethical scraping

---

### Model Training

```bash
# Model Training Service base URL
TRAINING_SERVICE_URL=http://model-training:8007

# LoRA adapter rank
TRAINING_LORA_RANK=16

# LoRA alpha parameter
TRAINING_LORA_ALPHA=32

# Learning rate
TRAINING_LEARNING_RATE=2e-4

# Number of training epochs
TRAINING_EPOCHS=3

# Batch size
TRAINING_BATCH_SIZE=4
```

**Notes:**
- LoRA reduces trainable parameters from billions to millions
- Batch size 4 works for 80GB GPUs (reduce if OOM)
- 3 epochs typical for 5K-10K sample datasets

---

### Langfuse (LLM Observability)

```bash
# Langfuse service URL
LANGFUSE_HOST=http://langfuse:3001

# Langfuse public API key
# Get from: http://langfuse:3001/dashboard → Settings → API Keys
LANGFUSE_PUBLIC_KEY=<key>

# Langfuse secret API key
LANGFUSE_SECRET_KEY=<key>
```

**Notes:**
- Langfuse tracks all LLM calls for cost/usage analytics
- Create workspace first, then generate API keys
- Keys are read from Langfuse web dashboard

---

### Session Management

```bash
# Session idle timeout (seconds)
SESSION_IDLE_TIMEOUT_SECONDS=1800

# Maximum conversation turns before truncation
SESSION_MAX_TURNS=50

# Maximum tokens to keep in conversation context
SESSION_CONTEXT_WINDOW_TOKENS=4096
```

**Notes:**
- 1800s = 30 minutes idle timeout
- Sessions auto-deleted after 50 turns (prevents memory bloat)
- Context window 4096 tokens ≈ recent 8-10 exchanges

---

### Data Retention

```bash
# Conversation retention (days)
RETENTION_CONVERSATIONS_DAYS=90

# User feedback retention (days)
RETENTION_FEEDBACK_DAYS=365

# Audit log retention (days, RFP requires 2 years)
RETENTION_AUDIT_LOG_DAYS=730

# Analytics retention (days)
RETENTION_ANALYTICS_DAYS=365

# Translation cache retention (days)
RETENTION_TRANSLATION_CACHE_DAYS=30
```

**Notes:**
- Audit logs: 730 days = 2 years (RFP compliance)
- Feedback: 365 days for model training dataset
- Conversations: 90 days balances privacy with analytics
- Auto-cleanup runs daily at 2 AM UTC

---

### Rate Limits (Requests per Minute per Role)

```bash
# Admin rate limit (full API access)
RATE_LIMIT_ADMIN=120

# Editor rate limit (document + config management)
RATE_LIMIT_EDITOR=90

# Viewer rate limit (read-only analytics)
RATE_LIMIT_VIEWER=30

# API Consumer rate limit (widget/external API)
RATE_LIMIT_API_CONSUMER=60
```

**Notes:**
- Rate limits applied per user per minute
- Limits are enforced by Redis at API Gateway
- Burst requests rejected with 429 status

---

### NGINX / TLS

```bash
# Domain for SSL certificate
NGINX_DOMAIN=culture.gov.in

# Path to SSL certificate (inside container)
NGINX_SSL_CERT_PATH=/etc/nginx/ssl/cert.pem

# Path to SSL private key (inside container)
NGINX_SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# CORS allowed origins
CORS_ALLOWED_ORIGINS=https://culture.gov.in,https://www.culture.gov.in
```

**Notes:**
- Certificate path relative to NGINX container filesystem
- Mount certs as Docker secrets in production
- CORS origins restrict cross-origin requests

---

### GPU Requirements

```bash
# Minimum NVIDIA driver version
NVIDIA_DRIVER_MIN_VERSION=535

# Minimum CUDA version
CUDA_MIN_VERSION=12.1
```

**Notes:**
- Checked at container startup
- Failed checks return health status = degraded

---

## Generating Secure Values

### Random Keys

```bash
# 256-bit hex key
python -c "import secrets; print(secrets.token_hex(32))"

# URL-safe base64 string
python -c "import secrets; print(secrets.token_urlsafe(32))"

# UUID
python -c "import uuid; print(uuid.uuid4())"
```

### Sample .env File

Create `/.env` at project root:

```bash
# Example .env file (CHANGE ALL PASSWORDS)
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ragqa
POSTGRES_USER=ragqa_user
POSTGRES_PASSWORD=secure_postgres_password_change_me_32_chars_long

LANGFUSE_PG_HOST=langfuse-postgres
LANGFUSE_PG_PORT=5433
LANGFUSE_PG_DB=langfuse
LANGFUSE_PG_USER=langfuse_user
LANGFUSE_PG_PASSWORD=secure_langfuse_password_change_me_32_chars

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_password_change_me_32_chars_long
REDIS_DB_CACHE=0
REDIS_DB_RATE_LIMIT=1
REDIS_DB_SESSION=2
REDIS_DB_TRANSLATION=3

MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_COLLECTION_TEXT=ministry_text
MILVUS_COLLECTION_IMAGE=ministry_images

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=secure_minio_password_change_me_32_chars
MINIO_BUCKET_DOCUMENTS=documents
MINIO_BUCKET_MODELS=models
MINIO_BUCKET_BACKUPS=backups
MINIO_USE_SSL=false

JWT_SECRET_KEY=jwt_secret_key_256_bits_hex_format_a1b2c3d4e5f6g7h8
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

LLM_SERVICE_URL=http://llm-service:8002
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq
LLM_GPU_MEMORY_UTILIZATION=0.85
LLM_MAX_MODEL_LEN_STANDARD=8192
LLM_MAX_MODEL_LEN_LONGCTX=131072
LLM_MAX_MODEL_LEN_MULTIMODAL=8192

RAG_SERVICE_URL=http://rag-service:8001
RAG_EMBEDDING_MODEL=BAAI/bge-m3
RAG_VISION_EMBEDDING_MODEL=google/siglip-so400m-patch14-384
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_K=5
RAG_CONFIDENCE_THRESHOLD=0.65
RAG_CACHE_TTL_SECONDS=3600

SPEECH_SERVICE_URL=http://speech-service:8003
SPEECH_STT_MODEL=ai4bharat/indicconformer-hi-en
SPEECH_TTS_HINDI_MODEL=ai4bharat/indic-tts-hindi
SPEECH_TTS_ENGLISH_MODEL=coqui/tts-english
SPEECH_SAMPLE_RATE=16000

TRANSLATION_SERVICE_URL=http://translation-service:8004
TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B
TRANSLATION_CACHE_TTL_SECONDS=86400

OCR_SERVICE_URL=http://ocr-service:8005
OCR_TESSERACT_LANG=hin+eng
OCR_EASYOCR_LANGS=hi,en

INGESTION_SERVICE_URL=http://data-ingestion:8006
INGESTION_SCRAPE_INTERVAL_HOURS=24
INGESTION_MAX_CONCURRENT_SPIDERS=4
INGESTION_RESPECT_ROBOTS_TXT=true

TRAINING_SERVICE_URL=http://model-training:8007
TRAINING_LORA_RANK=16
TRAINING_LORA_ALPHA=32
TRAINING_LEARNING_RATE=2e-4
TRAINING_EPOCHS=3
TRAINING_BATCH_SIZE=4

LANGFUSE_HOST=http://langfuse:3001
LANGFUSE_PUBLIC_KEY=pk-lf-change-me
LANGFUSE_SECRET_KEY=sk-lf-change-me

SESSION_IDLE_TIMEOUT_SECONDS=1800
SESSION_MAX_TURNS=50
SESSION_CONTEXT_WINDOW_TOKENS=4096

RETENTION_CONVERSATIONS_DAYS=90
RETENTION_FEEDBACK_DAYS=365
RETENTION_AUDIT_LOG_DAYS=730
RETENTION_ANALYTICS_DAYS=365
RETENTION_TRANSLATION_CACHE_DAYS=30

RATE_LIMIT_ADMIN=120
RATE_LIMIT_EDITOR=90
RATE_LIMIT_VIEWER=30
RATE_LIMIT_API_CONSUMER=60

NGINX_DOMAIN=culture.gov.in
NGINX_SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
NGINX_SSL_KEY_PATH=/etc/nginx/ssl/key.pem
CORS_ALLOWED_ORIGINS=https://culture.gov.in,https://www.culture.gov.in

NVIDIA_DRIVER_MIN_VERSION=535
CUDA_MIN_VERSION=12.1
```

---

## Validation

After creating `.env`, validate syntax:

```bash
# Check for common errors
grep -E "^[^=]+=.*=$|^[^=]+=\s*$" .env && echo "Found suspicious lines"

# Count variables
wc -l .env

# Check specific variable
source .env && echo $APP_ENV
```

---

## Common Configuration Mistakes

### Mistake: Using localhost

❌ `POSTGRES_HOST=localhost`
✓ `POSTGRES_HOST=postgres` (Docker service name)

### Mistake: Missing password

❌ `REDIS_PASSWORD=` (empty)
✓ `REDIS_PASSWORD=secure_password_32_chars_long`

### Mistake: Wrong model names

❌ `LLM_MODEL_STANDARD=llama-3` (incorrect)
✓ `LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ` (correct)

### Mistake: Invalid rate limits

❌ `RATE_LIMIT_ADMIN=0` (would block all admin requests)
✓ `RATE_LIMIT_ADMIN=120` (reasonable limit)

---

**Next:** Proceed to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) to deploy the system with these configurations.
