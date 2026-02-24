# Shared Package

Python package `rag-shared` with common utilities, models, and clients used by all services.

## Key Files

- `src/rag_shared/enums/language.py` — 23 language codes (hi, en, ta, te, kn, ml, mr, gu, pa, bn, or, as, etc.)
- `src/rag_shared/models/` — Pydantic request/response models (ChatRequest, SearchResult, FeedbackInput, etc.)
- `src/rag_shared/services/s3_client.py` — S3Client (boto3 wrapper for upload, download, delete)
- `src/rag_shared/services/redis_client.py` — Redis connection pool and helpers
- `src/rag_shared/services/http_client.py` — Async HTTP client with retry logic
- `src/rag_shared/services/sanitizer.py` — Input validation (SQL injection, XSS prevention)
- `src/rag_shared/services/encryption.py` — AES-256 encryption for sensitive data
- `src/rag_shared/middleware/logging.py` — Structlog JSON configuration
- `src/rag_shared/middleware/metrics.py` — Prometheus metric collectors
- `src/rag_shared/config.py` — Centralized Pydantic BaseSettings

## Pydantic Models

- ChatRequest, ChatResponse — chat endpoints
- SearchRequest, SearchResult — semantic search
- FeedbackInput — user feedback
- DocumentMetadata — document with language tags
- TranslationRequest/Response — translation
- OCRRequest/Result — OCR
- UserModel, RoleModel — RBAC (admin, editor, viewer, api_consumer)

## Installation

```bash
pip install -e ./shared
```

## Usage

```python
from rag_shared.enums import Language
from rag_shared.models import ChatRequest
from rag_shared.services import S3Client, RedisClient
from rag_shared.middleware import logger
```

## Known Issues

1. **S3 filename** — `s3_client.py` contains S3Client class.
2. **Language mismatch** — Enum supports 23 languages but some services only support subset.
