### STREAM 3: API Gateway (FastAPI) + Semantic Router

**Agent Goal:** Build the central FastAPI application with all route definitions, middleware, authentication, rate limiting, and the **Semantic Router** that routes queries to the appropriate LLM based on query type.

**Files to create:**
```
api-gateway/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, lifespan, CORS, middleware
│   ├── config.py                   # Pydantic settings (reads env vars)
│   ├── dependencies.py             # Shared deps (DB session, Redis, auth)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py         # Token-bucket via Redis (configurable per-role limits)
│   │   ├── audit_logger.py         # Log every request to audit_log (sanitize PII before logging)
│   │   ├── language_detector.py    # Detect input language (langdetect/fasttext, handles code-mixed Hindi-English)
│   │   ├── request_id.py           # X-Request-ID propagation
│   │   └── rbac.py                 # RBAC permission-checking middleware (JWT claims → roles/permissions tables)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py          # JWT create/verify for admin
│   │   ├── api_key.py              # API key validation for widget
│   │   └── models.py               # Auth Pydantic models
│   ├── router_engine/
│   │   ├── __init__.py
│   │   ├── semantic_router.py      # Classifies query → route to correct model
│   │   ├── routes.py               # Route definitions (factual→Llama, long→Mistral, visual→Gemma)
│   │   └── embeddings.py           # Lightweight encoder for route classification
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py                 # POST /api/v1/chat (conversational chatbot)
│   │   ├── chat_stream.py          # POST /api/v1/chat/stream (SSE streaming)
│   │   ├── search.py               # GET /api/v1/search (unified semantic search)
│   │   ├── voice.py                # POST /api/v1/voice/stt, /api/v1/voice/tts
│   │   ├── translate.py            # POST /api/v1/translate
│   │   ├── documents.py            # CRUD /api/v1/documents
│   │   ├── feedback.py             # POST /api/v1/feedback
│   │   ├── analytics.py            # GET /api/v1/analytics/*
│   │   ├── health.py               # GET /api/v1/health
│   │   ├── admin.py                # Admin routes (config, users, sessions)
│   │   └── ocr.py                  # POST /api/v1/ocr/upload
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py                 # ChatRequest, ChatResponse, Source
│   │   ├── search.py               # SearchRequest, SearchResponse, SearchResult (with multimedia)
│   │   ├── voice.py                # STTRequest, TTSRequest, AudioResponse
│   │   ├── translate.py            # TranslateRequest, TranslateResponse
│   │   ├── document.py             # DocumentUpload, DocumentMeta
│   │   ├── feedback.py             # FeedbackCreate, FeedbackResponse
│   │   ├── analytics.py            # AnalyticsSummary, QueryStats
│   │   └── common.py               # Pagination, ErrorResponse, Language enum
│   ├── services/
│   │   ├── __init__.py
│   │   ├── rag_client.py           # HTTP client → RAG service
│   │   ├── llm_client.py           # HTTP client → LLM service(s) — routes via Semantic Router
│   │   ├── speech_client.py        # HTTP client → Speech service
│   │   ├── translation_client.py   # HTTP client → Translation service
│   │   ├── ocr_client.py           # HTTP client → OCR service
│   │   ├── ingestion_client.py     # HTTP client → Data Ingestion service
│   │   ├── cache_service.py        # Redis caching layer
│   │   └── data_retention.py       # Configurable data retention (auto-purge aged conversations, feedback, audit logs)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py           # AsyncPG pool / SQLAlchemy async
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── crud.py                 # DB operations
│   └── utils/
│       ├── __init__.py
│       ├── language.py             # Language detection (langdetect/fasttext)
│       ├── langfuse_client.py      # Langfuse tracing integration
│       └── metrics.py              # Prometheus metrics exposition
├── tests/
│   ├── conftest.py
│   ├── test_chat.py
│   ├── test_search.py
│   ├── test_semantic_router.py
│   ├── test_voice.py
│   ├── test_documents.py
│   └── test_health.py
└── alembic/
    ├── alembic.ini
    └── versions/
```

**API Endpoints Summary:**

| Method | Endpoint | Interface | Description |
|---|---|---|---|
| POST | `/api/v1/chat` | Chatbot | Conversational query → RAG-augmented response |
| POST | `/api/v1/chat/stream` | Chatbot | SSE streaming chat response |
| GET | `/api/v1/search` | **Search Page** | Unified semantic search with AI summaries, multimedia, events |
| GET | `/api/v1/search/suggest` | **Search Page** | Auto-complete suggestions |
| POST | `/api/v1/voice/stt` | Both | Audio → text transcription |
| POST | `/api/v1/voice/tts` | Both | Text → synthesized audio |
| POST | `/api/v1/translate` | Both | Translate text between Indian languages |
| POST | `/api/v1/documents/upload` | Admin | Upload document for ingestion |
| GET | `/api/v1/documents` | Admin | List ingested documents |
| DELETE | `/api/v1/documents/{id}` | Admin | Remove document (+ cascade Milvus cleanup) |
| POST | `/api/v1/feedback` | Both | Submit user feedback (chat or search) |
| POST | `/api/v1/ocr/upload` | Admin | Upload image/scan for OCR |
| GET | `/api/v1/analytics/summary` | Admin | Dashboard metrics |
| GET | `/api/v1/analytics/queries` | Admin | Query analytics |
| GET | `/api/v1/health` | Internal | Health check all services |
| POST | `/api/v1/admin/login` | Admin | Admin JWT login |
| GET | `/api/v1/admin/config` | Admin | System configuration |
| POST | `/api/v1/admin/scrape/trigger` | Admin | Trigger web scrape job |

**Semantic Router logic:**
- Factual / short-context queries → **Llama 3.1 8B** (fast, efficient)
- Long-document / summarization queries → **Mistral NeMo 12B** (128K context)
- Image/multimodal queries → **Gemma 3** (vision-language)
- Translation requests → **IndicTrans2** (dedicated translation model)

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: call downstream services at exact URLs listed (rag-service:8001, llm-service:8002, speech-service:8003, translation-service:8004, ocr-service:8005, data-ingestion:8006, model-training:8007)
- §3 Environment Variables: read all `*_SERVICE_URL`, `JWT_*`, `REDIS_*`, `POSTGRES_*`, `SESSION_*`, `RATE_LIMIT_*`, `RETENTION_*`, `RAG_CONFIDENCE_THRESHOLD`, `CORS_ALLOWED_ORIGINS`, `LANGFUSE_*` variables
- §4 Error Response Format: ALL error responses must use the exact `{"error": {"code": "...", "message": "...", "details": {}, "request_id": "..."}}` format from §4
- §5 Health Check Format: `/api/v1/health` must aggregate health from all downstream services using the format from §5
- §6 Log Format: use structured JSON logging via `rag_shared.middleware.logging`
- §7 Request ID: generate UUID v4 `X-Request-ID`, propagate to all downstream calls, return in response headers
- §8 Inter-Service API Contracts: use exact request/response schemas from §8.1-8.7 for all downstream calls
- §12 RBAC: enforce roles/permissions as defined in §12
- §13 Chatbot Fallback: use exact fallback messages from §13

---

## Agent Prompt

### Agent 3: API Gateway + Semantic Router
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Use exact service URLs from §1, error format from §4, health format from §5,
API contracts from §8, RBAC from §12, fallback messages from §13.

Build a FastAPI API gateway with:
- Semantic Router: classifies queries and routes to correct LLM
  (factual→Llama 3.1 8B, long-context→Mistral NeMo 12B,
   visual→Gemma 3, translation→IndicTrans2)
- Routes for: /api/v1/chat (conversational chatbot), /api/v1/chat/stream (SSE),
  /api/v1/search (unified semantic search with AI summaries + multimedia),
  /api/v1/search/suggest (auto-complete), /api/v1/voice/stt, /api/v1/voice/tts,
  /api/v1/translate, /api/v1/documents (CRUD), /api/v1/feedback,
  /api/v1/ocr/upload, /api/v1/analytics/*, /api/v1/health,
  /api/v1/admin/* (login, config, scrape trigger)
- JWT auth with RBAC middleware: validate JWT claims against roles/permissions
  tables. 4 roles: admin, editor, viewer, api_consumer.
- Redis rate limiting (token-bucket), audit logging, language detection, CORS
- Langfuse tracing integration for all LLM calls
- OpenAPI: enable Swagger UI at /api/v1/docs and ReDoc at /api/v1/redoc.
  Add openapi_tags metadata for all route groups.
- Feedback→Sentiment pipeline: when /api/v1/feedback receives submission,
  async call LLM with sentiment prompt, store sentiment_score and
  sentiment_label back to feedback table.
- Chatbot fallback: if RAG retrieval confidence < threshold OR guardrails
  flag the response, return graceful message: "I'm unable to find an answer.
  Please contact the Ministry helpline at [number] or email [address]."
- Session lifecycle: 30-min idle timeout, context window truncation
  (keep last N turns within token limit), session resumption via session_id.
- Pydantic models for SearchResult (with multimedia, events, AI summary)
- Per-role rate limits: read rate limits from system_config table per role
  (e.g., api_consumer: 60 req/min, viewer: 30 req/min). Configurable via admin.
- Data retention service: configurable retention periods per data type
  (conversations: 90 days, feedback: 1 year, audit_log: 2 years). Auto-purge
  via scheduled background task. Periods stored in system_config table.
- API key management: generate/revoke API keys for api_consumer role.
  Key rotation, expiration, usage tracking in api_keys table.
- Language detection: use langdetect/fasttext, handle code-mixed Hindi-English.
- Shadow DOM CORS: configure CORS allowlist for culture.gov.in embedding.
```

