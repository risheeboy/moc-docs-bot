# RAG-Shared: Shared Python Library

Shared libraries and utilities used across all backend services for the RAG-based Hindi QA system (Ministry of Culture, Government of India).

## Features

### Models (`rag_shared.models`)
- **Language Enum**: ISO 639-1 language codes for all 23 Indian languages + English
- **Error Response**: Standardized error format (§4 of Shared Contracts)
- **Health Check**: Service health status responses (§5)
- **Chat Models**: ChatMessage, Source for conversational AI
- **Search Models**: SearchResult, MultimediaResult, EventResult
- **Document Models**: Document metadata
- **Pagination**: PaginatedRequest, PaginatedResponse

### Clients (`rag_shared.clients`)
- **BaseHTTPClient**: Async HTTP client with automatic retry, X-Request-ID propagation
- **RedisClient**: Redis cache operations (JSON serialization support)
- **PostgresClient**: Async PostgreSQL connection pool
- **MilvusClient**: Vector database operations
- **MinIOClient**: Object storage operations (S3-compatible)

### Middleware (`rag_shared.middleware`)
- **JSON Logging**: Structured logging with structlog (§6 of Shared Contracts)
  - Automatic request ID propagation
  - Service name binding
  - ISO 8601 timestamps
- **Prometheus Metrics**: HTTP metrics instrumentation (§11)
  - Request count, latency, size metrics
  - Service-specific metrics (RAG, LLM, Speech, etc.)

### Security (`rag_shared.security`)
- **AES Encryption**: AES-256-GCM for data at rest
  - Authenticated encryption
  - Random nonce generation
- **Input Sanitizer**: XSS/injection/PII detection
  - Remove script tags and HTML
  - Detect SQL/command injection
  - Mask PII in logs (Aadhaar, phone, email)

### Hindi Language Utilities (`rag_shared.hindi`)
- **Unicode Normalizer**: NFC/NFD/NFKC/NFKD normalization
  - Nukta diacritics handling
  - Quote/number normalization
- **Hindi Tokenizer**: Sentence/word/character tokenization
  - Handles Devanagari sentence markers (।, ॥)
- **Hindi Stopwords**: Common stopword list for filtering

### Configuration (`rag_shared.config`)
Complete Pydantic Settings classes for all services:
- App settings
- Database connections (PostgreSQL, Milvus)
- Cache (Redis)
- Object storage (MinIO)
- LLM/RAG/Speech/Translation/OCR services
- JWT, session, rate limit settings

## Installation

```bash
pip install -e .
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=rag_shared

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Usage Examples

### Models
```python
from rag_shared.models.language import Language
from rag_shared.models.errors import ErrorResponse, ErrorDetail
from rag_shared.models.chat import ChatMessage, Source

# Language validation
lang = Language.validate("hi")
print(lang.script)  # "Devanagari"

# Error response
error = ErrorResponse(
    error=ErrorDetail(
        code="INVALID_REQUEST",
        message="Invalid input",
        request_id="550e8400-e29b-41d4-a716-446655440000"
    )
)
```

### Clients
```python
from rag_shared.clients.redis_client import RedisClient

# Redis cache
redis = RedisClient("redis://redis:6379", db=0)
await redis.connect()
await redis.set_json("query:123", {"result": "data"}, ttl=3600)
data = await redis.get_json("query:123")
await redis.disconnect()

# Context manager
async with RedisClient("redis://redis:6379") as redis:
    await redis.set("key", "value")
```

### Logging
```python
from rag_shared.middleware.logging import setup_json_logging, get_logger

# Setup JSON logging for service
setup_json_logging("api-gateway", log_level="INFO")

# Get logger with context
logger = get_logger(__name__)
logger.info("Request processed", user_id="123", latency_ms=234)
```

### Security
```python
from rag_shared.security.encryption import AESEncryption
from rag_shared.security.sanitizer import InputSanitizer

# Encryption
cipher = AESEncryption()
encrypted = cipher.encrypt("secret data")
decrypted = cipher.decrypt(encrypted)

# Input sanitization
sanitized = InputSanitizer.sanitize("<script>alert('xss')</script>")
safe = InputSanitizer.is_safe(user_input)

# Remove PII for logging
clean = InputSanitizer.remove_pii("My phone: 9876543210")  # "My phone: [PHONE]"
```

### Hindi Processing
```python
from rag_shared.hindi.normalizer import normalize_hindi
from rag_shared.hindi.tokenizer import tokenize_hindi
from rag_shared.hindi.stopwords import filter_stopwords

# Normalize Hindi text
normalized = normalize_hindi("नमस्ते", form="NFC")

# Tokenize
sentences = tokenize_hindi("नमस्ते। यह एक परीक्षण है।", level="sentence")
words = tokenize_hindi("नमस्ते विश्व", level="word", remove_stopwords=True)
```

## Dependencies

### Core
- `pydantic==2.10.*`: Data validation
- `pydantic-settings==2.7.*`: Configuration management
- `httpx==0.28.*`: Async HTTP client
- `structlog==24.4.*`: Structured logging
- `prometheus-client==0.21.*`: Metrics

### Services
- `redis==5.2.*`: Redis client
- `asyncpg==0.30.*`: Async PostgreSQL
- `pymilvus==2.4.*`: Milvus vector DB
- `minio==7.2.*`: MinIO object storage
- `python-jose[cryptography]==3.3.*`: JWT + encryption

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_language.py::test_language_enum_values

# Generate coverage report
pytest --cov=rag_shared --cov-report=html
```

## Project Structure

```
shared/
├── pyproject.toml
├── README.md
├── src/rag_shared/
│   ├── __init__.py
│   ├── config.py                    # Configuration classes
│   ├── models/
│   │   ├── __init__.py
│   │   ├── language.py              # Language enum
│   │   ├── errors.py                # Error response models
│   │   ├── health.py                # Health check models
│   │   ├── chat.py                  # Chat/RAG models
│   │   ├── search.py                # Search result models
│   │   ├── document.py              # Document models
│   │   └── pagination.py            # Pagination models
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── base_client.py           # Base HTTP client
│   │   ├── redis_client.py          # Redis helper
│   │   ├── postgres_client.py       # PostgreSQL helper
│   │   ├── milvus_client.py         # Milvus helper
│   │   └── minio_client.py          # MinIO helper
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py               # JSON logging setup
│   │   └── metrics.py               # Prometheus metrics
│   ├── security/
│   │   ├── __init__.py
│   │   ├── encryption.py            # AES encryption
│   │   └── sanitizer.py             # Input sanitization
│   └── hindi/
│       ├── __init__.py
│       ├── normalizer.py            # Unicode normalization
│       ├── tokenizer.py             # Hindi tokenizer
│       └── stopwords.py             # Stopword list
└── tests/
    ├── __init__.py
    ├── test_language.py
    ├── test_hindi_normalizer.py
    └── test_encryption.py
```

## Shared Contracts Reference

This package implements:
- **§3**: Environment Variables via `rag_shared.config`
- **§4**: Error Response Format (ErrorResponse, ErrorDetail)
- **§5**: Health Check Format (HealthResponse, DependencyHealth)
- **§6**: Structured JSON Logging (middleware/logging.py)
- **§7**: Request ID Propagation (BaseHTTPClient)
- **§9**: Language Codes (Language enum)
- **§10**: Pagination (PaginatedRequest, PaginatedResponse)
- **§11**: Prometheus Metrics (middleware/metrics.py)

## License

Apache 2.0
