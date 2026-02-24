# API Gateway - Stream 3 Implementation

FastAPI-based API Gateway for the RAG-based Hindi QA system serving India's Ministry of Culture.

## Quick Start

### Requirements
- Python 3.11+
- PostgreSQL 16+
- Redis 7+

### Installation

```bash
pip install -r requirements.txt
```

### Environment Setup

Copy and configure `.env`:
```bash
cp .env.example .env
```

Key variables:
```
APP_ENV=production
POSTGRES_HOST=postgres
REDIS_HOST=redis
JWT_SECRET_KEY=<generate-secure-random>
CORS_ALLOWED_ORIGINS=https://culture.gov.in
```

### Running

**Development:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Docker:**
```bash
docker build -t api-gateway:1.0.0 .
docker run -p 8000:8000 --env-file .env --network rag-network api-gateway:1.0.0
```

### Database Migration

```bash
alembic upgrade head
```

## Documentation

- **API Endpoints**: See [API_ENDPOINTS.md](API_ENDPOINTS.md)
- **Implementation Details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **OpenAPI Docs**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Architecture

### Core Components

1. **Semantic Router**: Routes queries to appropriate LLM model
   - Factual → Llama 3.1 8B (fast)
   - Long-context → Mistral NeMo 12B (128K context)
   - Multimodal → Gemma 3 (vision)
   - Translation → IndicTrans2

2. **Authentication**: JWT + API Keys
   - Admin/Editor/Viewer roles
   - api_consumer role for widgets

3. **Middleware Chain**:
   - Request ID propagation
   - Audit logging (PII-safe)
   - Language detection
   - Rate limiting (per-role)
   - RBAC enforcement

4. **Service Clients**: HTTP clients to 7 downstream services
   - RAG (vector retrieval)
   - LLM (model inference)
   - Speech (STT/TTS)
   - Translation
   - OCR
   - Ingestion (web scraping)

### API Routes (11 routers)

| Category | Endpoints |
|----------|-----------|
| Chat | `/chat`, `/chat/stream` |
| Search | `/search`, `/search/suggest` |
| Voice | `/voice/stt`, `/voice/tts` |
| Translation | `/translate`, `/translate/batch`, `/translate/detect` |
| Documents | `/documents`, `/documents/{id}` |
| Feedback | `/feedback` |
| OCR | `/ocr/upload` |
| Analytics | `/analytics/summary`, `/analytics/queries` |
| Admin | `/admin/login`, `/admin/config`, `/admin/scrape/*` |
| Health | `/health` |

## Standards Compliance

All implementation follows the Shared Contracts from the Design Document:

- ✓ Service Registry (§1) - All 7 downstream services
- ✓ Error Format (§4) - Standard `{"error": {...}}`
- ✓ Health Check (§5) - Aggregates all dependencies
- ✓ Logging (§6) - Structured JSON via structlog
- ✓ Request ID (§7) - X-Request-ID propagation
- ✓ API Contracts (§8) - Exact schemas per service
- ✓ RBAC (§12) - 4 roles with endpoint-level permissions
- ✓ Fallback Messages (§13) - Hindi/English
- ✓ Dependencies (§14) - Pinned versions

## Testing

```bash
pytest tests/ -v --asyncio-mode=auto
```

Test coverage:
- Health checks
- Chat endpoints
- Search functionality
- Semantic router classification
- Voice I/O
- Document CRUD

## Monitoring

### Prometheus Metrics
- `http_requests_total` - Request counter
- `http_request_duration_seconds` - Latency
- `llm_tokens_generated_total` - Token usage
- `rag_retrieval_duration_seconds` - Retrieval latency

Endpoint: http://localhost:8000/metrics

### Langfuse Integration
Traces LLM calls for observability. Configure in .env:
```
LANGFUSE_PUBLIC_KEY=<key>
LANGFUSE_SECRET_KEY=<key>
```

## Configuration

All settings in `app/config.py`:
- Database: PostgreSQL async connection
- Cache: Redis connection pooling
- Services: All 7 downstream service URLs
- Auth: JWT secret, algorithm, expiry
- Rate limits: Per-role request limits
- Data retention: Auto-purge policies

## Security

- **PII Masking**: Query params sanitized in audit logs
- **Token Rotation**: JWT expiry + refresh tokens
- **API Key Hashing**: SHA256 storage
- **CORS**: Configured for culture.gov.in
- **Rate Limiting**: Per-role, Redis-backed

## Development Guidelines

### Code Style
- Type hints throughout
- Docstrings for all public functions
- Async/await for I/O operations
- Error handling with logging

### Adding New Endpoints

1. Create route in `app/routers/<module>.py`
2. Define Pydantic models in `app/models/<module>.py`
3. Add to OpenAPI tags
4. Add tests in `tests/test_<module>.py`
5. Update API_ENDPOINTS.md

### Database Queries

Use CRUD classes from `app/db/crud.py`:
```python
from app.db.crud import SessionCRUD

session = await SessionCRUD.get(db, session_id)
await SessionCRUD.update_activity(db, session_id)
```

### Service Clients

Initialize and use in routers:
```python
rag_client = RAGClient(settings.rag_service_url)
response = await rag_client.query(...)
```

## Troubleshooting

### Database Connection Failed
- Check PostgreSQL is running
- Verify connection string in .env
- Run migrations: `alembic upgrade head`

### Redis Connection Failed
- Check Redis is running on port 6379
- Verify REDIS_HOST in .env

### Rate Limit Errors
- Check Redis is accessible
- Verify rate_limit_* values in config

### Authentication Errors
- Check JWT_SECRET_KEY is set
- Verify X-API-Key or Authorization header
- Check token expiry

## Performance Tips

1. **Caching**: Results cached in Redis by default
2. **Database**: Use pagination for large result sets
3. **Streaming**: Use `/chat/stream` for long responses
4. **Batch Operations**: Use batch endpoints for translation
5. **Index**: Add DB indexes for frequently queried columns

## Contributing

All code must:
- Pass type checking: `mypy app/`
- Have 80%+ test coverage
- Follow pydantic conventions
- Include docstrings
- Handle async properly

## Support

For issues, see:
1. Logs in `/var/log/api-gateway/`
2. Prometheus metrics at `/metrics`
3. OpenAPI docs at `/api/v1/docs`

---

**Version**: 1.0.0  
**Python**: 3.11  
**Framework**: FastAPI 0.115+  
**License**: MIT (Government of India)
