# Infrastructure Requirements

**Source:** Requirements.pdf page 10

## Hosting Environment

- **NIC/MeitY Data Centre** — System must be hosted on infrastructure empanelled by NIC (National Informatics Centre) or MeitY (Ministry of Electronics and Information Technology)
- **On-premise deployment** — no cloud-hosted services; all services run within the data centre
- **Data sovereignty** — all data must remain within India's borders at all times

## Hardware Requirements

### Compute
- **GPU-equipped Linux machine** — for AI model inference (LLM, embeddings, STT, TTS, translation, OCR)
- Must support CUDA for GPU acceleration
- Docker + NVIDIA Container Toolkit for GPU passthrough to containers

### Storage
- **Minimum 10TB storage** capacity for:
  - Document storage (crawled web content, PDFs, images, videos)
  - Vector database storage (embeddings)
  - Model weights storage
  - Database storage (PostgreSQL)
  - Backup storage
- **MinIO object storage** configured with 10TB capacity
- Backup volumes must be on **separate physical storage** from primary

### Network
- High-bandwidth connection to serve concurrent users
- Internal network for inter-service communication
- External-facing NGINX reverse proxy with TLS termination

## Deployment Architecture

- **All services as Docker containers** — no bare-metal installations
- Docker images sourced from **hub.docker.com**
- Single-machine deployment (all containers on one host)
- Docker Compose for orchestration
- Health checks and automatic restart policies for all containers
- NVIDIA Container Toolkit for GPU access in containers

## Monitoring & Observability

- **Prometheus** for metrics collection
- **Grafana** for dashboards and alerting
- **Loki** for centralized log aggregation
- **Langfuse** for LLM-specific observability (token usage, latency, quality)
- Health check endpoints for all services (GET /health)

## Backup & Disaster Recovery

- **Automated daily backups:**
  - PostgreSQL: pg_dump (daily incremental, weekly full)
  - Milvus: vector DB snapshots
  - MinIO: bucket sync to backup storage
  - Redis: RDB dump
- **Disaster Recovery targets:**
  - RTO (Recovery Time Objective): < 4 hours
  - RPO (Recovery Point Objective): < 1 hour
- Backup storage on separate physical media
- Documented recovery procedures
