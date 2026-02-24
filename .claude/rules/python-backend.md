---
description: Python backend service conventions
paths:
  - "api-gateway/**/*.py"
  - "rag-service/**/*.py"
  - "llm-service/**/*.py"
  - "speech-service/**/*.py"
  - "translation-service/**/*.py"
  - "ocr-service/**/*.py"
  - "data-ingestion/**/*.py"
  - "model-training/**/*.py"
  - "shared/**/*.py"
---

# Python Backend Rules

All microservices follow these conventions:

## FastAPI Endpoints

- All endpoints: `async def`, type-hinted params and returns
- Error handling: use ErrorResponse model from shared lib (never raw HTTPException)
- Health check: implement `GET /health` per contract format (returns `{"status": "healthy|unhealthy", "checks": {...}}`)
- Documentation: FastAPI auto-generates OpenAPI at `/docs`

## Configuration

- Config: Pydantic BaseSettings in each service's `app/config.py`
- New env vars: add to both `shared/config.py` AND `Implementation_Plan/01_Shared_Contracts.md` §3
- Secrets: AWS Secrets Manager (never hardcode)
- Template: check `.env.example` for required vars

## Logging & Observability

- Logging: `import structlog; logger = structlog.get_logger(__name__)`
- Format: JSON structured logs only (no plain text)
- Langfuse integration: wrap LLM calls with `@langfuse.observe()`

## Data Access & Storage

- S3 client: use boto3 via `S3Client` from `rag_shared.clients.s3_client`
- Redis: use SSL when `REDIS_SSL=true` (AWS ElastiCache in-transit encryption)
- Database: SQLAlchemy 2.0 async ORM only (never raw SQL)
- No SQL injection: never use f-strings in queries

## Testing & Quality

- Tests: pytest, minimum 80% coverage
- Fixtures: in conftest.py, reusable across test modules
- Docstrings: Google style, 3+ lines for public functions

## Imports & Naming

- Imports: absolute (`from rag_shared.models import ...`), never relative
- Functions: snake_case (e.g., `process_documents`)
- Classes: PascalCase (e.g., `DocumentProcessor`)
- Constants: UPPER_CASE

## Example Function

```python
async def query_documents(
    query: str,
    language: str = "hi",
    top_k: int = 5
) -> list[DocumentResult]:
    """Search documents by semantic similarity.

    Args:
        query: User input string
        language: ISO 639-1 code (23 supported languages)
        top_k: Number of results to return

    Returns:
        List of ranked documents with scores
    """
```
