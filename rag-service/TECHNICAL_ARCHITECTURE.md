# RAG Service Technical Architecture

## Service Overview

The RAG Service is a FastAPI-based microservice that provides retrieval-augmented generation capabilities for the Ministry of Culture QA system. It handles document ingestion, embedding, retrieval, and context assembly for both chatbot and search interfaces.

```
┌─────────────────────────────────────────────────────────────┐
│                  API Gateway (port 8000)                    │
└─────────────┬───────────────────────────────────────────────┘
              │
         ┌────▼─────┐
         │ RAG Query │ (port 8001)
         │  Service  │
         └─┬─────────┘
           │
     ┌─────┼─────────────────────┐
     │     │                     │
┌────▼──┐ ┌▼──────────┐ ┌───────▼────┐
│Milvus │ │  Redis    │ │   MinIO    │
│VecDB  │ │  Cache    │ │  Storage   │
└───────┘ └───────────┘ └────────────┘
```

## Request/Response Flow

### Query Endpoint (Chatbot)

```
POST /query
├─ Generate Cache Key (query + filters → SHA256)
│
├─ Cache Hit? → Return cached QueryResponse
│
└─ Cache Miss:
   ├─ EmbedderService.embed_text(query)
   │  └─ BGE-M3 model → dense vector (768-dim)
   │
   ├─ VectorStoreService.search_text(embedding, top_k)
   │  └─ Milvus IVF_FLAT search → N candidates
   │
   ├─ RerankerService.rerank(query, candidates, rerank_top_k)
   │  └─ Cross-encoder → reranked results
   │
   ├─ ContextBuilder.build_context(chunks)
   │  └─ Assemble with [Source N] citations
   │
   ├─ Calculate confidence (avg of scores)
   │
   ├─ CacheService.set(cache_key, response, TTL)
   │  └─ Serialize to JSON → Redis
   │
   └─ Return QueryResponse {context, sources, confidence, cached}
```

### Search Endpoint (Semantic Search)

```
POST /search
├─ Generate Cache Key (query + filters + page + page_size)
│
├─ Cache Hit? → Return cached SearchResponse
│
└─ Cache Miss:
   ├─ RetrieverService.retrieve(query, language, top_k*2)
   │  (Same pipeline as /query)
   │
   ├─ Paginate results[(page-1)*page_size : page*page_size]
   │
   ├─ Extract multimedia from results
   │
   ├─ Extract events from metadata
   │
   ├─ CacheService.set(cache_key, response, TTL)
   │
   └─ Return SearchResponse {results, multimedia, events, pagination, cached}
```

### Ingest Endpoint (Document Processing)

```
POST /ingest
├─ HindiAwareTextSplitter.split_text(content)
│  └─ Respect sentence boundaries → chunks
│
├─ EmbedderService.embed_batch(chunks)
│  └─ BGE-M3 model → dense vectors (768-dim each)
│
├─ Prepare Milvus documents
│  ├─ id (UUID)
│  ├─ document_id (reference)
│  ├─ chunk_index
│  ├─ title, content, source_url, source_site
│  ├─ language, content_type
│  ├─ dense_embedding (vector)
│  ├─ metadata_json
│  └─ created_at (timestamp)
│
├─ VectorStoreService.upsert_text(documents)
│  └─ Milvus insert/update → ministry_text collection
│
├─ Process images (if provided):
│  ├─ VisionEmbedderService.embed_images_batch(images)
│  │  └─ SigLIP model → image vectors (384-dim each)
│  │
│  └─ VectorStoreService.upsert_images(image_docs)
│     └─ Milvus insert/update → ministry_images collection
│
├─ CacheService.invalidate_all()
│  └─ Flush rag:query:* entries from Redis
│
└─ Return IngestResponse {document_id, chunk_count, milvus_ids, status}
```

## Data Models

### Milvus Collections

#### ministry_text (Text Embeddings)
```sql
CREATE COLLECTION ministry_text (
  id: VARCHAR PRIMARY KEY,
  document_id: VARCHAR,
  chunk_index: INT32,
  title: VARCHAR(512),
  content: VARCHAR(4096),
  source_url: VARCHAR(1024),
  source_site: VARCHAR(256),
  language: VARCHAR(10),
  content_type: VARCHAR(50),
  dense_embedding: FLOAT_VECTOR DIM 768,  -- BGE-M3
  metadata_json: VARCHAR(2048),
  created_at: INT64
)

INDEX: dense_embedding (IVF_FLAT, metric=L2, nlist=1024)
```

#### ministry_images (Image Embeddings)
```sql
CREATE COLLECTION ministry_images (
  id: VARCHAR PRIMARY KEY,
  image_url: VARCHAR(1024),
  alt_text: VARCHAR(512),
  source_url: VARCHAR(1024),
  source_site: VARCHAR(256),
  image_embedding: FLOAT_VECTOR DIM 384,  -- SigLIP
  metadata_json: VARCHAR(1024),
  created_at: INT64
)

INDEX: image_embedding (IVF_FLAT, metric=L2, nlist=1024)
```

### Redis Cache Keys

```
Key Format: rag:query:{SHA256(query|language|filters|page|page_size)}
Value: JSON-serialized QueryResponse or SearchResponse
TTL: RAG_CACHE_TTL_SECONDS (default 3600 seconds)
DB: REDIS_DB_CACHE (default 0)
```

### MinIO Bucket Structure

```
documents/
├── raw/                           # Scraped HTML/PDF/DOCX
│   └── {source_site}/{doc_id}.{ext}
├── processed/                     # Extracted text
│   └── {doc_id}.txt
├── images/                        # Extracted images
│   └── {doc_id}/{img_id}.{ext}
└── thumbnails/                    # Generated thumbnails
    └── {doc_id}_thumb.jpg
```

## Service Dependencies

### External Services
- **Milvus** (vector DB): `http://milvus:19530`
- **Redis** (cache): `redis:6379`
- **MinIO** (storage): `minio:9000`

### Python Dependencies
- **FastAPI** (0.115.x) — Web framework
- **Pydantic** (2.10.x) — Request/response validation
- **sentence-transformers** (3.0.x) — BGE-M3 model
- **pymilvus** (2.4.x) — Milvus Python SDK
- **redis** (5.2.x) — Redis client
- **minio** (7.2.x) — MinIO client
- **torch** (2.2.x) — Deep learning (GPU support)
- **torchvision** (0.17.x) — Vision utilities
- **marker-pdf** (0.3.x) — High-quality PDF parsing
- **prometheus-client** (0.21.x) — Metrics

## Error Handling Strategy

### Standard Error Response
```python
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {...},  # Optional context
    "request_id": "uuid"  # For tracing
  }
}
```

### HTTP Status Codes
- **400**: INVALID_REQUEST — Malformed input
- **500**: INTERNAL_ERROR — Unexpected server error
- **502**: UPSTREAM_ERROR — Milvus/Redis connection issue
- **503**: SERVICE_UNAVAILABLE — Critical dependency down

### Request ID Propagation
1. Generated by API Gateway if missing
2. Extracted from X-Request-ID header
3. Included in all logs and error responses
4. Passed to downstream services

## Performance Optimization

### Embedding Optimization
- Batch encoding for multiple texts (batch_size=32)
- GPU acceleration via torch
- Model caching in memory
- Dimension reduction not applied (full 768-dim for better quality)

### Search Optimization
- IVF_FLAT indexing (faster than HNSW for this scale)
- Milvus connection pooling
- Top-K over-retrieval for reranking
- Hybrid search fusion (dense + sparse)

### Cache Optimization
- SHA256 hash for keys (deterministic, short)
- Pipeline caching (full response object)
- Selective invalidation (pattern-based)
- TTL-based automatic expiration

### Retrieval Optimization
- Sentence-aware text chunking
- Chunk overlap for context continuity
- Metadata filtering in Milvus
- Cross-encoder reranking for quality

## Monitoring & Observability

### Health Checks
```
GET /health
├─ Milvus connectivity test
├─ Redis connectivity test
└─ Response: status + dependency latencies
```

### Prometheus Metrics
```
http_requests_total{method, endpoint, status_code}
http_request_duration_seconds{method, endpoint}
http_request_size_bytes{method, endpoint}
http_response_size_bytes{method, endpoint}

rag_retrieval_duration_seconds{operation}
rag_cache_hit_total
rag_cache_miss_total
rag_documents_ingested_total
rag_chunks_created_total
rag_retrieval_results{operation}
```

### Structured Logging
```json
{
  "timestamp": "2026-02-24T10:30:00.123Z",
  "level": "INFO",
  "service": "rag-service",
  "request_id": "uuid",
  "message": "Query completed",
  "logger": "app.routers.query",
  "extra": {
    "latency_ms": 245,
    "result_count": 5,
    "confidence": 0.87
  }
}
```

## Deployment

### Docker Image
- Base: python:3.11-slim
- Build: Copy requirements + app code
- Expose: Port 8001
- Start: uvicorn app.main:app --host 0.0.0.0 --port 8001

### Environment Variables
```bash
# Milvus
MILVUS_HOST=milvus
MILVUS_PORT=19530

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure>
REDIS_DB_CACHE=0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<key>

# RAG
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_K=5
RAG_CACHE_TTL_SECONDS=3600
```

### Resource Requirements
- **CPU**: 2+ cores (embedding is CPU-bound)
- **Memory**: 4GB+ (models loaded in memory)
- **GPU**: Optional but recommended (NVIDIA GPU with CUDA 12.1+)
- **Disk**: 2GB+ (model cache)

## Testing Strategy

### Unit Tests
- Model validation (Pydantic)
- Text splitting (Hindi + English)
- Embedding dimension consistency
- Cache key generation

### Integration Tests (when services available)
- End-to-end query pipeline
- Search with pagination
- Document ingestion
- Cache hit/miss
- Error responses

### Performance Tests
- Batch embedding throughput
- Search latency (various top-k)
- Cache effectiveness
- Memory usage under load

## Security Considerations

### Input Validation
- Pydantic validation on all requests
- Language code whitelist (ISO 639-1)
- File size limits (implicit via chunk processing)
- SQL injection prevention (no raw queries)

### Data Privacy
- No PII logged (email, phone, names)
- Request truncation in logs
- Cache key hashing (query not visible)
- Secure Redis password handling

### Network Security
- No credentials in code
- Environment variable configuration
- Internal network (rag-network)
- MinIO SSL optional (false for internal)

## Scalability Considerations

### Horizontal Scaling
- Stateless design (all state in Milvus/Redis/MinIO)
- Multiple instances behind load balancer
- Shared vector database
- Shared cache

### Vertical Scaling
- GPU acceleration for embeddings
- Batch processing for efficiency
- Connection pooling for databases
- Memory mapping for large models

### Future Improvements
1. Async request handling for /ingest
2. Streaming response for /search (Server-Sent Events)
3. Batch API for bulk operations
4. Caching at multiple levels (local, Redis, Milvus)
5. Request batching for embeddings
6. Fine-tuned models for domain-specific search
