# API Gateway

FastAPI gateway on port 8000. Central request router with semantic routing, RBAC middleware, and rate limiting.

## Key Files

- `app/main.py` — FastAPI application entry point
- `app/routers/` — Endpoints: chat, search, documents, voice, feedback, analytics, admin, health
- `app/middleware/` — rbac.py, rate_limiter.py, request_id.py
- `app/services/` — HTTP clients for 7 downstream services
- `app/config.py` — Configuration (Pydantic settings)

## Endpoints

- `POST /chat` — Chat completions (streaming)
- `GET /search` — Semantic search
- `POST /documents/*` — Document management (list, upload, delete)
- `POST /voice/*` — Speech processing (STT/TTS)
- `POST /feedback` — User feedback (rating, comments)
- `GET /analytics/*` — Analytics queries
- `POST /admin/*` — Admin operations (role mgmt, system config)
- `GET /health` — Health check

## Dependencies

- Downstream: RAG (8001), LLM (8002), Speech (8003), Translation (8004), OCR (8005), Data Ingestion (8006), Model Training (8007)
- Databases: PostgreSQL, Redis
- Service discovery: Cloud Map `ragqa.local`

## Known Issues

1. **Rate limiter race condition** — In-memory counter has race under high concurrency. Fix: use Redis Lua script.
2. **CORS misconfiguration** — Uses `allow_origins=["*"]`. Fix: restrict to ALB domain.
3. **Health check inefficiency** — Creates new DB connection per call. Reuse connection pool.
