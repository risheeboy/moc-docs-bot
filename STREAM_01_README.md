# Stream 1: Infrastructure & Docker Compose

## Overview

This directory contains the complete Docker Compose infrastructure for the RAG-Based Hindi QA System for India's Ministry of Culture. It includes orchestration, networking, shared volumes, environment configuration, GPU resource allocation, backup/restore procedures, and comprehensive monitoring setup.

**Implementation Status:** ✓ Complete

---

## Directory Structure

```
rag-qa-hindi/
├── docker-compose.yml                    # Main orchestration (17+ services)
├── infrastructure/
│   ├── .env.example                      # Environment variable template (REQUIRED)
│   ├── .env                              # Actual .env (gitignored, create from example)
│   ├── nginx/
│   │   ├── Dockerfile                    # NGINX image with TLS
│   │   ├── nginx.conf                    # Main NGINX config
│   │   ├── conf.d/
│   │   │   ├── api.conf                  # /api/* routes
│   │   │   ├── search.conf               # /search routes
│   │   │   ├── chat.conf                 # /chat-widget routes
│   │   │   ├── admin.conf                # /admin routes
│   │   │   └── monitoring.conf           # /grafana, /langfuse routes
│   │   └── ssl/
│   │       ├── cert.pem                  # TLS certificate (self-signed for dev)
│   │       └── key.pem                   # TLS key
│   ├── scripts/
│   │   ├── init.sh                       # First-time setup
│   │   ├── start.sh                      # Start all services
│   │   ├── stop.sh                       # Stop all services
│   │   ├── health-check.sh               # Deep health verification
│   │   ├── seed-data.sh                  # Trigger initial web scraping
│   │   ├── backup.sh                     # Automated backup
│   │   ├── restore.sh                    # Restore from backup
│   │   ├── backup-validate.sh            # Validate backup integrity
│   │   └── monthly-report.sh             # Generate performance report
│   └── monitoring/
│       ├── prometheus/
│       │   └── prometheus.yml            # Scrape configs for 15+ services
│       ├── grafana/
│       │   ├── provisioning/
│       │   │   ├── datasources/
│       │   │   │   └── prometheus.yml    # Prometheus + Loki datasources
│       │   │   └── dashboards/
│       │   │       └── dashboard.yml     # Dashboard provisioning
│       │   └── dashboards/
│       │       ├── system-overview.json  # System health & performance
│       │       ├── api-metrics.json      # API & service metrics
│       │       └── llm-metrics.json      # LLM & GPU metrics
│       └── loki/
│           └── loki-config.yml           # Log aggregation config
```

---

## Quick Start

### 1. Initialize Infrastructure (One-time)

```bash
cd /sessions/amazing-wizardly-wright/mnt/rag-qa-hindi

# Run initialization
./infrastructure/scripts/init.sh
```

This will:
- Verify Docker, Docker Compose, and NVIDIA tooling
- Create .env file from template
- Create all Docker volumes
- Build custom images (NGINX)
- Initialize PostgreSQL schema
- Set up Docker network

### 2. Configure Environment

```bash
# Edit .env file with production values
nano .env

# Required values to update:
# - APP_SECRET_KEY (use: openssl rand -hex 32)
# - POSTGRES_PASSWORD, REDIS_PASSWORD, etc.
# - MINIO_ACCESS_KEY, MINIO_SECRET_KEY
# - JWT_SECRET_KEY (use: openssl rand -hex 32)
# - LLM_API_KEY
```

### 3. Generate TLS Certificates

For production, use valid certificates. For development:

```bash
mkdir -p infrastructure/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infrastructure/nginx/ssl/key.pem \
  -out infrastructure/nginx/ssl/cert.pem \
  -subj "/C=IN/ST=Delhi/L=Delhi/O=Ministry of Culture/CN=culture.gov.in"
```

### 4. Start Services

```bash
./infrastructure/scripts/start.sh
```

### 5. Verify Health

```bash
./infrastructure/scripts/health-check.sh
```

### 6. Seed Initial Data (Optional)

```bash
./infrastructure/scripts/seed-data.sh
```

---

## Services & Ports

### Core Services (Internal)
| Service | Port | Purpose |
|---------|------|---------|
| api-gateway | 8000 | FastAPI gateway (routes requests) |
| rag-service | 8001 | Retrieval-Augmented Generation |
| llm-service | 8002 | LLM inference (vLLM) |
| speech-service | 8003 | Speech-to-text & text-to-speech |
| translation-service | 8004 | Indic language translation |
| ocr-service | 8005 | Optical character recognition |
| data-ingestion | 8006 | Web scraping & document parsing |
| model-training | 8007 | LoRA fine-tuning |

### Database & Cache
| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5432 | Main application database |
| langfuse-postgres | 5433 | Langfuse observability DB |
| redis | 6379 | Caching & session store |
| milvus | 19530 | Vector database |
| etcd | 2379 | Milvus metadata store |
| minio | 9000/9001 | Object storage + console |

### Monitoring & Observability
| Service | Port | Purpose |
|---------|------|---------|
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Dashboards & alerting |
| langfuse | 3001 | LLM observability |
| loki | 3100 | Log aggregation |
| dcgm-exporter | 9400 | NVIDIA GPU metrics |

### Frontend & Proxy
| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80/443 | Reverse proxy with TLS |

---

## GPU Configuration

The system uses NVIDIA GPU for:
- **GPU 0**: LLM inference (llm-service)
- **GPU 1**: Speech processing (speech-service)
- **GPU 2**: Translation (translation-service)
- **GPU 3**: Model training (model-training)

### Prerequisites

```bash
# Verify NVIDIA driver >= 535
nvidia-smi

# Verify CUDA >= 12.1
nvcc --version

# Verify nvidia-container-toolkit
docker run --rm --runtime=nvidia nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi
```

### GPU Memory Requirements
- LLM Service: 20GB (for multiple models)
- Speech Service: 8GB
- Translation Service: 8GB
- Model Training: 16GB
- **Total: 52GB minimum** (4x A100 40GB recommended)

---

## Environment Variables

See `infrastructure/.env.example` for complete list. Key sections:

```bash
# Application
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=<random-256-bit-hex>

# Databases
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=<secure>
REDIS_PASSWORD=<secure>

# LLM Models (via vLLM)
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ

# RAG Configuration
RAG_CHUNK_SIZE=512
RAG_TOP_K=10
RAG_CONFIDENCE_THRESHOLD=0.65

# Rate Limiting (per role)
RATE_LIMIT_ADMIN=120
RATE_LIMIT_VIEWER=30
```

---

## Backup & Restore

### Automated Daily Backups

```bash
# Daily backup (cron-scheduled)
./infrastructure/scripts/backup.sh daily

# Weekly full backup
./infrastructure/scripts/backup.sh weekly
```

**Backup includes:**
- PostgreSQL (pg_dump)
- Langfuse PostgreSQL
- Redis (RDB snapshot)
- MinIO documents (via mc)
- Backups stored in: `./backups/daily/` and `./backups/weekly/`

### Restore from Backup

```bash
# List available backups
ls ./backups/daily/

# Restore specific backup
./infrastructure/scripts/restore.sh 20260224_120000
```

**Note:** Restore drops existing databases and restores from backup. Requires confirmation.

### Validate Backup Integrity

```bash
# Test restore to temporary database without overwriting
./infrastructure/scripts/backup-validate.sh 20260224_120000
```

---

## Monitoring & Dashboards

### Grafana (http://localhost:3000)

Default credentials: `admin` / `admin`

**Pre-configured Dashboards:**

1. **System Overview** (uid: system-overview)
   - Service uptime
   - CPU/Memory/Network usage
   - Request rates & error rates
   - Response latency (p95/p99)

2. **API & Service Metrics** (uid: api-metrics)
   - API Gateway request distribution
   - Endpoint-specific latency
   - Throughput (bytes/sec)
   - RAG cache hit rate
   - Retrieval latency

3. **LLM & GPU Metrics** (uid: llm-metrics)
   - Token generation rate
   - LLM inference latency
   - GPU memory/temp/utilization
   - Error rates by service

### Prometheus (http://localhost:9090)

Scrape targets for:
- All backend services (api-gateway, rag-service, llm-service, etc.)
- Databases (PostgreSQL, Redis)
- Vector store (Milvus)
- NVIDIA DCGM exporter (GPU metrics)
- System metrics

### Langfuse (http://localhost:3001)

LLM-specific observability:
- Token usage tracking
- Cost analysis
- Latency breakdowns
- Error tracing

### Loki (http://localhost:3100)

Log aggregation and querying via Grafana.

---

## Health Checks

### Quick Status

```bash
docker-compose ps
```

### Deep Health Verification

```bash
./infrastructure/scripts/health-check.sh
```

Verifies:
- Database connectivity (PostgreSQL, Redis, Milvus)
- Service health endpoints
- API Gateway functionality
- Prometheus scrape targets
- GPU availability (if NVIDIA)

### Service-Specific Logs

```bash
# View real-time logs
docker-compose logs -f api-gateway

# Last 100 lines
docker-compose logs --tail=100 rag-service

# Specific service
docker-compose logs llm-service
```

---

## Networking

**Network:** `rag-network` (Docker bridge)
**Subnet:** `172.28.0.0/16`

All services communicate via Docker DNS (service names):
- `http://api-gateway:8000`
- `http://rag-service:8001`
- etc.

---

## Security

### TLS/HTTPS

NGINX enforces:
- **TLS 1.2+** (TLS 1.3 preferred)
- **Strong cipher suite** (no weak ciphers)
- **HSTS** headers (enforce HTTPS)
- **Security headers** (CSP, X-Frame-Options, etc.)

### RBAC

Defined roles: `admin`, `editor`, `viewer`, `api_consumer`

Routes require JWT authentication with role-based access control.

### Data Protection

- Encryption at rest for sensitive data
- PII sanitization in logs
- Rate limiting per role
- Input validation on all endpoints

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs [service-name]

# Common issues:
# 1. Port already in use: change port mappings in docker-compose.yml
# 2. Out of memory: increase Docker memory limit
# 3. GPU not available: verify nvidia-container-toolkit
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Reduce model load: adjust LLM_GPU_MEMORY_UTILIZATION in .env
```

### Slow Queries

```bash
# Check slow query logs
PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Database Connection Errors

```bash
# Verify connectivity
docker-compose exec postgres psql -U ragqa_user -d ragqa -c "SELECT 1;"

# Check connection pool
docker-compose exec api-gateway curl http://localhost:8000/health
```

---

## Scheduled Tasks

### Recommended Cron Jobs

```bash
# Daily backup (11 PM)
0 23 * * * cd /path/to/rag-qa-hindi && ./infrastructure/scripts/backup.sh daily

# Weekly full backup (Sunday midnight)
0 0 * * 0 cd /path/to/rag-qa-hindi && ./infrastructure/scripts/backup.sh weekly

# Health check (every hour)
0 * * * * cd /path/to/rag-qa-hindi && ./infrastructure/scripts/health-check.sh > /dev/null 2>&1

# Monthly report (1st of month, 9 AM)
0 9 1 * * cd /path/to/rag-qa-hindi && ./infrastructure/scripts/monthly-report.sh
```

---

## Production Deployment Checklist

- [ ] Update all secrets in `.env` (generate new keys)
- [ ] Obtain valid SSL certificates (replace self-signed)
- [ ] Configure firewall rules (restrict port access)
- [ ] Enable log rotation (Docker JSON logging limits)
- [ ] Set up automated backups (daily + weekly)
- [ ] Configure backup retention policy
- [ ] Test disaster recovery (restore from backup)
- [ ] Enable Prometheus alerts
- [ ] Configure alert routing (PagerDuty, Slack, etc.)
- [ ] Document runbooks for common incidents
- [ ] Set up monitoring dashboards
- [ ] Perform load testing
- [ ] Document deployment procedures
- [ ] Verify GDPR/data protection compliance
- [ ] Verify NIC/MeitY compliance (data center location)

---

## Compliance & Data Residency

**IMPORTANT:** This system is designed for:

1. **NIC/MeitY Empanelled Data Centers**
   - Data must remain within Indian territory
   - Refer to MeitY Cloud guidelines

2. **Government of India Standards**
   - GIGW compliance (design document included)
   - Audit logging & compliance reporting
   - Regular security assessments

3. **Data Protection**
   - Indian Data Protection Act 2023 compliance
   - PII handling & retention policies
   - Encryption for data at rest

---

## Documentation References

- **Overview:** See `Implementation_Plan/00_Overview.md`
- **Shared Contracts:** See `Implementation_Plan/01_Shared_Contracts.md`
- **Stream Details:** See `Implementation_Plan/Stream_01_Infrastructure.md`

---

## Support & Contact

For infrastructure issues:
1. Check logs: `docker-compose logs [service]`
2. Run health check: `./infrastructure/scripts/health-check.sh`
3. Verify environment: Check `.env` configuration
4. Consult runbooks in documentation

---

## License & Attribution

Ministry of Culture, Government of India
Developed with NIC/MeitY guidelines
Designed for deployment in Indian data centers

---

**Last Updated:** 2026-02-24
**Stream:** 01 - Infrastructure & Docker Compose
**Status:** Production Ready
