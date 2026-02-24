### STREAM 10: Shared Libraries & Utilities

**Agent Goal:** Create shared Python packages used across all backend services.

**Files to create:**
```
shared/
├── pyproject.toml                  # Installable as `rag-shared` package
├── src/
│   └── rag_shared/
│       ├── __init__.py
│       ├── config.py               # Shared config (service URLs, feature flags)
│       ├── models/
│       │   ├── __init__.py
│       │   ├── language.py         # Language enum (all 22 scheduled Indian languages)
│       │   ├── chat.py             # Shared ChatMessage, Source models
│       │   ├── search.py           # SearchResult, MultimediaResult models
│       │   ├── document.py         # Document metadata models
│       │   └── health.py           # HealthStatus model
│       ├── clients/
│       │   ├── __init__.py
│       │   ├── base_client.py      # Base HTTP client with retry, timeout, circuit breaker
│       │   ├── redis_client.py     # Redis connection helper
│       │   ├── postgres_client.py  # Async PostgreSQL helper
│       │   ├── milvus_client.py    # Milvus connection helper
│       │   └── minio_client.py     # MinIO object storage helper
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── logging.py          # Structured JSON logging
│       │   └── metrics.py          # Prometheus metrics helpers
│       ├── security/
│       │   ├── __init__.py
│       │   ├── encryption.py       # AES encryption for PII at rest
│       │   └── sanitizer.py        # Input sanitization (XSS, injection)
│       └── hindi/
│           ├── __init__.py
│           ├── normalizer.py       # Unicode normalization for Devanagari
│           ├── tokenizer.py        # Hindi sentence tokenizer
│           └── stopwords.py        # Hindi stopword list
└── tests/
    ├── test_language.py
    ├── test_hindi_normalizer.py
    └── test_encryption.py
```

**No dependencies** — imported by Streams 3, 4, 5, 6, 7, 12, 13.

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §3 Environment Variables: `config.py` must define Pydantic Settings classes reading ALL env vars from §3.2
- §4 Error Response Format: define `ErrorResponse` and `ErrorDetail` Pydantic models exactly as in §4
- §5 Health Check Format: define `HealthResponse` and `DependencyHealth` models exactly as in §5
- §6 Log Format: `middleware/logging.py` must implement `setup_json_logging(service_name)` producing the exact JSON format from §6
- §7 Request ID: `clients/base_client.py` must propagate `X-Request-ID` header on all outbound HTTP calls
- §9 Language Codes: `models/language.py` must define Language enum with all 23 codes from §9
- §10 Conventions: all Pydantic models use `snake_case`, `ConfigDict(from_attributes=True)`, UUIDs as `uuid.UUID`
- §11 Prometheus Metrics: `middleware/metrics.py` must provide automatic HTTP metrics instrumentation (the 4 standard metrics from §11)
- §14 Python Versions: pinned dependency versions from §14 become this package's dependencies

---


---

## Agent Prompt

### Agent 10: Shared Libraries
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
This package implements the shared contracts. Models from §4-5, logging from §6,
request ID propagation from §7, language enum from §9, metrics from §11, deps from §14.
Create a Python package 'rag-shared' with:
- Language enum (all 22 scheduled Indian languages + English)
- Shared Pydantic models: ChatMessage, Source, SearchResult,
  MultimediaResult, EventResult, Document, HealthStatus
- Base HTTP client with retry/circuit-breaker
- Client helpers: Redis, PostgreSQL (async), Milvus, MinIO
- Structured JSON logging, Prometheus metrics helpers
- AES encryption utility, input sanitizer
- Hindi Unicode normalizer, Hindi sentence tokenizer, Hindi stopwords
```

