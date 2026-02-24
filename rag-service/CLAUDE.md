# RAG Service

FastAPI on port 8001. Semantic search and document retrieval via LlamaIndex + Milvus vector database.

## Key Files

- `app/main.py` — FastAPI application
- `app/services/indexer.py` — Document indexing into Milvus
- `app/services/retriever.py` — Query retrieval and ranking
- `app/services/embedder.py` — BGE-M3 embedding generation
- `app/services/reranker.py` — Result reranking
- `app/services/cache_service.py` — Redis query caching
- `app/config.py` — Configuration (Pydantic)

## Endpoints

- `POST /index/documents` — Index new documents
- `POST /search` — Semantic search (returns ranked results)
- `GET /retrieve/{doc_id}` — Fetch specific document
- `POST /batch-search` — Batch search multiple queries
- `GET /health` — Health check

## Dependencies

- Milvus (vector DB, 2 collections: ministry_text, ministry_images)
- Redis (query result cache, TTL 3600s)
- S3 (document storage bucket: ragqa-documents)
- BGE-M3 embeddings (1GB+, dense + sparse + ColBERT)
- SigLIP (vision embeddings for images)

## Known Issues

1. **Import bug in indexer.py** — Still imports S3Client instead of S3Client
2. **S3 filename** — `s3_client.py` contains boto3 code (misleading name)
3. **Model load error handling** — Embedder fails hard on load failure. Add try-catch.
4. **Cold start** — BGE-M3 model is slow on first request.
