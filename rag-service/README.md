# RAG Service (Stream 4)

Retrieval-Augmented Generation pipeline using LlamaIndex, Milvus, BGE-M3 embeddings, and SigLIP vision embeddings.

## Overview

The RAG Service handles:
- **Document Ingestion**: Chunking and embedding documents
- **Semantic Retrieval**: Hybrid search (dense + sparse) via Milvus
- **Query Processing**: Retrieval + reranking for chatbot context
- **Semantic Search**: Paginated results with multimedia and events
- **Caching**: Redis query result caching with TTL

## Architecture

```
Document → Text Splitter → BGE-M3 Embeddings → Milvus
                                  ↓
                          Vector Store (Hybrid Search)
                                  ↓
                          Cross-Encoder Reranker
                                  ↓
                          Context Builder
                                  ↓
                     Redis Cache (optional)
```

## API Endpoints

### Query (Chatbot Context Retrieval)
```http
POST /query
Content-Type: application/json

{
  "query": "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
  "language": "hi",
  "session_id": "uuid",
  "chat_history": [...],
  "top_k": 10,
  "rerank_top_k": 5,
  "filters": { ... }
}

Response: QueryResponse (context + sources + confidence)
```

### Search (Semantic Search with Results)
```http
POST /search
Content-Type: application/json

{
  "query": "Indian heritage sites",
  "language": "en",
  "page": 1,
  "page_size": 20,
  "filters": { ... }
}

Response: SearchResponse (results + multimedia + events + pagination)
```

### Ingest (Document Indexing)
```http
POST /ingest
Content-Type: application/json

{
  "document_id": "uuid",
  "title": "Document Title",
  "source_url": "https://...",
  "source_site": "example.com",
  "content": "Full text...",
  "content_type": "webpage",
  "language": "en",
  "metadata": { ... },
  "images": [ ... ]
}

Response: IngestResponse (chunk_count + milvus_ids)
```

### Health Check
```http
GET /health

Response: HealthResponse (status + dependencies)
```

### Metrics
```http
GET /metrics

Response: Prometheus metrics (text/plain)
```

## Services

### app/services/

- **embedder.py** — BGE-M3 dense embeddings
- **vision_embedder.py** — SigLIP image embeddings
- **vector_store.py** — Milvus client (search, upsert, delete)
- **retriever.py** — Query → embedding → search → rerank
- **reranker.py** — Cross-encoder reranking
- **context_builder.py** — Assemble context with citations
- **text_splitter.py** — Hindi-aware sentence chunking
- **cache_service.py** — Redis query result caching
- **indexer.py** — Full ingestion pipeline
- **minio_client.py** — MinIO S3 client

## Configuration

Read from environment variables:

```bash
# Milvus
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_COLLECTION_TEXT=ministry_text
MILVUS_COLLECTION_IMAGE=ministry_images

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<secure>
REDIS_DB_CACHE=0

# MinIO Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<key>
MINIO_BUCKET_DOCUMENTS=documents

# RAG Settings
RAG_EMBEDDING_MODEL=BAAI/bge-m3
RAG_VISION_EMBEDDING_MODEL=google/siglip-so400m-patch14-384
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=64
RAG_TOP_K=10
RAG_RERANK_TOP_K=5
RAG_CONFIDENCE_THRESHOLD=0.65
RAG_CACHE_TTL_SECONDS=3600
```

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Docker:
```bash
docker build -t rag-service .
docker run -p 8001:8001 \
  -e MILVUS_HOST=milvus \
  -e REDIS_HOST=redis \
  rag-service
```

## Testing

```bash
pytest tests/
```

Test files:
- `test_health.py` — Health check endpoint
- `test_text_splitter.py` — Hindi-aware text chunking
- `test_embedder.py` — BGE-M3 embeddings
- `test_api_models.py` — Request/response validation
- `test_cache_service.py` — Redis caching

## Metrics

Prometheus metrics exposed at `/metrics`:

- `http_requests_total` — Total HTTP requests (method, endpoint, status)
- `http_request_duration_seconds` — Request latency histogram
- `rag_retrieval_duration_seconds` — Retrieval latency
- `rag_cache_hit_total` — Cache hits
- `rag_cache_miss_total` — Cache misses
- `rag_documents_ingested_total` — Documents ingested
- `rag_chunks_created_total` — Chunks created

## Implementation Notes

1. **Hybrid Search**: BGE-M3 provides dense vectors + sparse lexical weights. Milvus performs vector similarity search. Reciprocal rank fusion can be added for sparse scoring.

2. **Reranking**: Cross-encoder (mmarco-mMiniLMv2-L12) reranks top-K results from dense search.

3. **Caching**: Query + filters → SHA256 hash → Redis key. TTL configurable. Invalidated on ingest.

4. **Text Chunking**: Respects Hindi/English sentence boundaries. 512-token chunks with 64-token overlap.

5. **Vision Search**: SigLIP embeds images in same space as text. Enables cross-modal retrieval.

6. **MinIO Storage**: Raw documents stored at `documents/raw/{site}/{doc_id}`, processed text at `documents/processed/`, images at `documents/images/`.

## Error Handling

Standard error response format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... },
    "request_id": "uuid"
  }
}
```

Error codes:
- `INVALID_REQUEST` (400) — Malformed request
- `INVALID_LANGUAGE` (400) — Unsupported language
- `INTERNAL_ERROR` (500) — Server error
- `UPSTREAM_ERROR` (502) — Milvus/Redis error
- `SERVICE_UNAVAILABLE` (503) — Service down

## Performance

Typical latencies (on GPU):
- Embedding 1 document: 100-200ms
- Milvus search (10 results): 20-50ms
- Reranking (10→5): 10-30ms
- Total query latency: 200-300ms (cached: <5ms)

## Future Enhancements

1. Sparse search integration (BM25)
2. Hypothetical document embeddings (HyDE)
3. Query expansion
4. Multi-hop reasoning
5. Document summarization before indexing
6. Dynamic retrieval (adaptive top-k)
