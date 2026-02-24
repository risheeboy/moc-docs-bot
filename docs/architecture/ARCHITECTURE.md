# System Architecture

**Version:** 1.0.0
**Last Updated:** February 24, 2026

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NGINX Reverse Proxy                       │
│                  (SSL/TLS, routing, load balancing)              │
└────┬──────────────┬─────────────┬────────────────┬──────────────┘
     │              │             │                │
┌────▼─────┐  ┌─────▼──────┐ ┌──▼──────┐  ┌──────▼────┐
│  Search  │  │Chat Widget │ │ Admin    │  │ Grafana   │
│  Page    │  │ (embedded) │ │Dashboard │  │Dashboards │
│ (React)  │  │  (React)   │ │(React)   │  │           │
└────┬─────┘  └─────┬──────┘ └──┬──────┘  └──────────┘
     │              │             │
     └──────┬───────┴─────────────┘
            │
    ┌───────▼──────────────┐
    │   API Gateway        │
    │   (FastAPI/Uvicorn)  │
    │  • Auth (JWT)        │
    │  • Rate limiting     │
    │  • Semantic routing  │
    └─┬──┬──┬──┬──┬──┬──┬─┘
      │  │  │  │  │  │  │
    ┌─▼┐┌▼─┐┌▼──┐┌────▼┐┌────┐┌───────┐
    │RAG││LLM││Spch││Trans││OCR ││Data   │
    │Svc││Svc││Svc ││ Svc ││Svc ││Ingest │
    └─┬┘└┬──┘└┬──┘└──┬─┘└─┬──┘└───┬──┘
      │   │    │      │     │       │
      │   │    │      │     │       │
    ┌─▼───▼────▼──────▼─────▼───────▼─┐
    │         GPU Compute Layer         │
    │  • Llama 3.1 (8B, vLLM)         │
    │  • Mistral NeMo (12B, vLLM)     │
    │  • Gemma 3 (12B, vLLM)          │
    │  • BAAI/BGE-M3 (embeddings)     │
    │  • IndicConformer (ASR)         │
    │  • IndicTrans2 (translation)    │
    │  • Tesseract + EasyOCR (OCR)    │
    └─┬──────────────────────────────┬┘
      │                              │
┌─────▼────────────────────────────▼──────┐
│         Data Layer (Docker Volumes)      │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐   │
│  │PostgreSQL│ │  Milvus  │ │ MinIO   │   │
│  │(metadata)│ │(vectors) │ │(objects)│   │
│  └─────────┘ └──────────┘ └─────────┘   │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐   │
│  │ Redis   │ │   etcd   │ │Langfuse │   │
│  │(cache)  │ │(Milvus)  │ │(LLM obs)│   │
│  └─────────┘ └──────────┘ └─────────┘   │
└──────────────────────────────────────────┘
```

---

## Component Descriptions

### Frontend (React SPAs)

**Chat Widget** (`chat-widget:80`)
- Embeddable chat interface
- Floating bubble widget
- Multi-turn conversations
- Voice I/O support
- Real-time streaming responses

**Search Page** (`search-page:80`)
- Full-page search interface
- Result ranking and filtering
- Image/video/event results
- Faceted navigation
- Pagination

**Admin Dashboard** (`admin-dashboard:80`)
- Staff management
- Document upload & management
- Analytics & reporting
- Model management
- System configuration

### API Gateway (FastAPI)

**Responsibilities:**
- User authentication (JWT)
- Rate limiting (per-role)
- Request routing to backend services
- Response aggregation
- Error handling
- Logging and monitoring

**Endpoints (25 total):**
- `/chat` — Single-turn chat
- `/chat/stream` — Streaming responses
- `/search` — Semantic search
- `/voice/stt` — Speech-to-text
- `/voice/tts` — Text-to-speech
- `/translate` — Translation
- `/ocr/upload` — OCR
- `/documents/*` — Document management
- `/admin/*` — Admin operations
- And 15+ more (see API_Reference.md)

### RAG Service

**Inputs:**
- User query (text)
- Chat history (for context)
- Filters (date, source, language)

**Process:**
1. Embed query using BAAI/BGE-M3 (1024-dim dense + sparse)
2. Retrieve top-K vectors from Milvus
3. Rerank using cross-encoder
4. Assemble context from top chunks
5. Cache result in Redis (1-hour TTL)

**Output:**
- Ranked documents with scores
- Assembled context text
- Confidence score
- Source metadata

### LLM Service (vLLM)

**Models:**
- `meta-llama/Llama-3.1-8B-Instruct-AWQ` (standard)
- `mistralai/Mistral-NeMo-Instruct-2407-AWQ` (long-context)
- `google/gemma-3-12b-it-awq` (multimodal)

**Features:**
- OpenAI-compatible API
- Streaming responses
- AWQ quantization (4-bit)
- LoRA adapter support
- Token counting

### Data Ingestion Pipeline

**Sources:**
- 30+ Ministry websites (culture.gov.in, asi.nic.in, etc.)
- Documents: HTML, PDF, DOCX, images

**Process:**
1. Scrapy crawls target URLs
2. Playwright handles JavaScript rendering
3. Documents stored in MinIO
4. Marker extracts text from PDFs
5. Sent to RAG service for embedding
6. Vectors stored in Milvus
7. Metadata in PostgreSQL

**Storage Structure (MinIO §16):**
```
documents/raw/          → Raw HTML/PDF files
documents/processed/    → Extracted text
documents/thumbnails/   → Generated previews
documents/images/       → Extracted images
```

### Database Layer

**PostgreSQL (metadata)**
- Documents table (title, URL, language, etc.)
- Conversations (for admin/analytics)
- User sessions
- Feedback & ratings
- Audit logs
- Chunks metadata (for RAG)

**Milvus (vector store)**
- ministry_text collection (1024-dim BGE-M3)
- ministry_images collection (768-dim SigLIP)
- Both collections indexed for fast retrieval

**Redis (cache)**
- Query result cache (1-hour TTL)
- Translation cache (24-hour TTL)
- Rate limiter counters (1-minute windows)
- Session store
- Database 0-3 (separate by purpose)

**MinIO (object storage)**
- Documents: 10TB allocated
- Models: 500GB allocated
- Backups: 2TB allocated

---

## Data Flow Diagrams

### Chat Flow (User Query → Response)

```
User Query (text/audio)
        ↓
[API Gateway]
    ↓ validate, auth, rate-limit
[Speech-to-Text] (if audio)
    ↓ transcribe → text
[Translate] (if needed)
    ↓ translate to English for retrieval
[RAG Service]
    ↓ 1. Embed query (BAAI/BGE-M3)
    ↓ 2. Search Milvus (top-10 vectors)
    ↓ 3. Rerank (top-5)
    ↓ 4. Check Redis cache
    ↓ 5. Assemble context
[LLM Service]
    ↓ 1. Format system + user + context prompts
    ↓ 2. Run inference (Llama/Mistral/Gemma)
    ↓ 3. Stream or batch return
[API Gateway]
    ↓ 1. Log conversation
    ↓ 2. Store in PostgreSQL
    ↓ 3. Cache in Redis
[Response] → User (text/audio + sources)
```

### Document Ingestion Flow

```
Target URLs (Ministry websites)
        ↓
[Data Ingestion Service]
    ↓ 1. Scrapy crawls (Playwright for JS)
    ↓ 2. Extracts HTML/PDF/DOCX
    ↓ 3. Stores raw in MinIO/documents/raw/
    ↓ 4. Parses with Marker
    ↓ 5. Stores text in MinIO/documents/processed/
[RAG Service]
    ↓ 1. Chunk text (512 tokens, overlap 64)
    ↓ 2. Embed chunks (BAAI/BGE-M3)
    ↓ 3. Insert vectors to Milvus
    ↓ 4. Store metadata in PostgreSQL
[Search Index Ready]
    ↓ Users can now search across new documents
```

### Admin Training Flow

```
[Admin] uploads training data (JSONL)
        ↓
[MinIO] stores at s3://models/training_data/
        ↓
[Model Training Service]
    ↓ 1. Download base model (Llama/Mistral)
    ↓ 2. Prepare LoRA adapters
    ↓ 3. Run training loop (3 epochs)
    ↓ 4. Save adapter + merged model
    ↓ 5. Store in MinIO/models/finetuned/
[Model Evaluation]
    ↓ 1. Run on eval dataset
    ↓ 2. Calculate F1, BLEU, hallucination rate
    ↓ 3. Store results in PostgreSQL
[Dashboard] shows metrics
```

---

## Service Dependencies

```
api-gateway (depends on):
  ├── postgres (metadata)
  ├── redis (cache, rate limit, sessions)
  ├── rag-service (document retrieval)
  ├── llm-service (text generation)
  ├── speech-service (STT/TTS)
  ├── translation-service (translate)
  ├── ocr-service (OCR)
  └── data-ingestion (job status)

rag-service (depends on):
  ├── milvus (vector search)
  ├── postgres (metadata)
  ├── redis (cache)
  └── minio (documents)

llm-service (depends on):
  ├── GPU (NVIDIA)
  └── model-cache (local disk)

data-ingestion (depends on):
  ├── postgres (track documents)
  ├── minio (store raw/processed)
  └── rag-service (ingest embeddings)

speech-service (depends on):
  ├── GPU (NVIDIA, optional)
  └── model-cache (weights)

milvus (depends on):
  └── etcd (consensus)
```

---

## Scaling Considerations

### Horizontal Scaling

**API Gateway:**
- Add multiple instances behind load balancer
- Share PostgreSQL, Redis, Milvus backends
- No per-instance state

**RAG Service:**
- Stateless service
- Scale to 2-4 instances with shared Milvus
- Cache hits reduce backend load

**LLM Service:**
- GPU-bound (can't scale horizontally on single GPU)
- Use model parallelism on multi-GPU if available
- Or deploy to additional GPU servers with separate vLLM

### Vertical Scaling

- Add more GPU memory (A100 80GB → multiple A100s)
- Increase PostgreSQL RAM for query caching
- Increase Redis memory for longer cache TTL
- Increase Milvus disk for larger vector indices

### Performance Tuning

- Increase `RAG_TOP_K` for recall vs. speed tradeoff
- Adjust `LLM_GPU_MEMORY_UTILIZATION` (0.70-0.85)
- Fine-tune Milvus index parameters (IVF, HNSW)
- Increase Redis cache TTL for frequently-searched documents

---

## Security Architecture

**Network Security:**
- NGINX TLS termination (certificate pinning)
- Docker network isolation (rag-network)
- PostgreSQL port 5432 internal only
- Milvus port 19530 internal only

**Authentication:**
- JWT tokens (HS256, 60-minute expiry)
- Refresh tokens for longer sessions
- Database of revoked tokens

**Authorization:**
- 4 roles: admin, editor, viewer, api_consumer
- RBAC checks on every endpoint
- Permissions table in PostgreSQL

**Data Encryption:**
- TLS for data in transit
- Passwords hashed with bcrypt
- Sensitive config in .env (not committed)

**Audit Logging:**
- All actions logged to PostgreSQL
- Structured JSON logs to Loki
- Accessible via admin dashboard
- 2-year retention per RFP

---

## Monitoring & Observability

**Metrics:** Prometheus
- HTTP latency, error rates
- GPU memory, temperature
- Database query times
- Cache hit rates

**Logs:** Loki + Promtail
- Structured JSON logs
- Full trace with request IDs
- Searchable by service, level, time

**Traces:** Langfuse (LLM only)
- LLM call tracing
- Cost tracking
- Token accounting
- Hallucination detection

**Dashboards:** Grafana
- Real-time system overview
- Alert configuration
- Custom queries and panels

---

**See also:**
- [DATA_FLOW.md](DATA_FLOW.md) — Detailed data flow diagrams
- [SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md) — Security controls
- [DEPLOYMENT_GUIDE.md](../deployment/DEPLOYMENT_GUIDE.md) — How to deploy this architecture

**Last Updated:** February 24, 2026
