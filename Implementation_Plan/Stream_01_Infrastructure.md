### STREAM 1: Infrastructure & Docker Compose

**Agent Goal:** Create the Docker Compose orchestration, networking, shared volumes, environment configuration, and GPU resource allocation.

**Files to create:**
Note: `docker-compose.yml` lives at the **project root** (`rag-qa-hindi/docker-compose.yml`), not inside `infrastructure/`.

```
infrastructure/
├── .env.example                    # Environment variable template
├── .env                            # Actual env (gitignored)
├── nginx/
│   ├── Dockerfile
│   ├── nginx.conf                  # Main config with upstream backends
│   ├── conf.d/
│   │   ├── api.conf                # /api/* → API Gateway
│   │   ├── search.conf             # /search → Search SPA
│   │   ├── chat.conf               # /chat-widget/* → Chat Widget assets
│   │   ├── admin.conf              # /admin → Admin Dashboard
│   │   └── monitoring.conf         # /grafana, /langfuse
│   └── ssl/                        # Self-signed certs for dev
├── scripts/
│   ├── init.sh                     # First-time setup (create volumes, pull images, verify GPU)
│   ├── start.sh                    # Start all services
│   ├── stop.sh                     # Graceful shutdown
│   ├── health-check.sh             # Verify all services are healthy (deep checks)
│   ├── seed-data.sh                # Trigger initial web scrape + ingestion
│   ├── backup.sh                   # Automated backup (PG, Milvus, S3, Redis)
│   ├── restore.sh                  # Restore from backup with validation
│   ├── backup-validate.sh          # Verify backup integrity (restore to temp, checksum)
│   └── monthly-report.sh           # Generate monthly performance report from Prometheus API
└── monitoring/
    ├── prometheus/
    │   └── prometheus.yml           # Scrape targets for all services
    ├── grafana/
    │   ├── provisioning/
    │   │   ├── datasources/
    │   │   │   └── prometheus.yml
    │   │   └── dashboards/
    │   │       └── dashboard.yml
    │   └── dashboards/
    │       ├── system-overview.json
    │       ├── api-metrics.json
    │       └── llm-metrics.json
    └── loki/
        └── loki-config.yml
```

**Key requirements:**
- Single `docker-compose.yml` with all services (17+ containers)
- GPU passthrough via NVIDIA Container Toolkit for: llm-service, speech-service, translation-service, model-training
- Shared Docker network (`rag-network`) for inter-service communication
- Named volumes for: `postgres-data`, `milvus-data`, `redis-data`, `minio-data`, `model-cache`, `uploaded-docs`, `langfuse-data`, `backup-data`
- Health checks on every service (deep health checks: verify downstream dependencies, not just HTTP 200)
- Resource limits (memory/CPU) per container
- Restart policies (`unless-stopped`)
- NGINX routes: `/api/*` → API Gateway, `/search` → Search SPA, `/` → Chat Widget embed page, `/admin` → Admin Dashboard, `/grafana` → Grafana, `/langfuse` → Langfuse
- NGINX TLS: enforce TLS 1.2+ minimum, configure cipher suite allowlist, add HSTS header
- Services to include: nginx, api-gateway, rag-service, llm-service (vLLM), speech-service, translation-service, ocr-service, data-ingestion, model-training, postgres, redis, milvus (standalone), etcd (Milvus dependency), minio, prometheus, grafana, langfuse, langfuse-postgres (dedicated PG for Langfuse), loki
- GPU prerequisites: document required NVIDIA driver version (≥535), CUDA toolkit version (≥12.1), and nvidia-container-toolkit in `.env.example` comments
- Backup scripts must include backup validation (restore test to temp DB, verify checksum)
- Prometheus config must include NVIDIA DCGM exporter for GPU metrics (utilization, memory, temperature)
- Grafana alerting rules for: service downtime, response time > 5s, error rate spikes, GPU memory > 90%, storage > 80%, failed backups
- Monthly performance report generation script (cron job → markdown report from Prometheus/Grafana API)

**No dependencies on other streams.**

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: use exact Docker service names and ports listed there
- §2 Docker Network & Volumes: network name `rag-network`, volume names as listed
- §3 Environment Variables: `.env.example` must contain ALL variables from §3.2
- §11 Prometheus Metrics: scrape all services at `<service>:<port>/metrics`
- §17 Docker Labels: apply `com.ragqa.*` labels to all services
- DCGM Exporter: `dcgm-exporter` on port 9400
- Grafana: port 3000, Langfuse: port 3001, Prometheus: port 9090, Loki: port 3100

---

## Agent Prompt

### Agent 1: Infrastructure
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Use exact service names, ports, volume names, and env vars from 01_Shared_Contracts.md §1-3.

Create Docker Compose infrastructure for a multi-service RAG application.
docker-compose.yml at project root (rag-qa-hindi/docker-compose.yml).
Services: nginx, api-gateway, rag-service, llm-service (vLLM), speech-service,
translation-service, ocr-service, data-ingestion, model-training, postgres,
redis, milvus (standalone + etcd), minio, prometheus, grafana, langfuse,
langfuse-postgres (dedicated PG for Langfuse), loki.
GPU passthrough for: llm-service, speech-service, translation-service,
model-training.
All base images from hub.docker.com.
NGINX routing: /api/* → api-gateway, /search → search-page SPA,
/chat-widget → chat widget, /admin → admin dashboard, /grafana → grafana,
/langfuse → langfuse.
Include health checks, named volumes (postgres-data, milvus-data, minio-data,
redis-data, model-cache, langfuse-data), resource limits, restart policies.
BACKUP: Add cron-based backup scripts for PostgreSQL (pg_dump), Milvus
snapshots, S3 bucket sync, Redis RDB dump. Daily incremental, weekly full.
Include backup validation script (restore to temp DB, verify checksum).
S3 must be provisioned with 10TB capacity.
NIC/MeitY: Document that Docker host must be in NIC/MeitY-empanelled
Data Centre in India. Add compliance notes in comments.
NGINX TLS: enforce TLS 1.2+, configure cipher suite allowlist, HSTS header.
GPU prerequisites: document required NVIDIA driver (≥535), CUDA (≥12.1),
nvidia-container-toolkit in .env.example comments.
Monitoring: Prometheus must scrape NVIDIA DCGM exporter for GPU metrics.
Grafana alerts: service down, response time >5s, error spikes, GPU >90%,
storage >80%, failed backups. Include monthly-report.sh for automated
monthly performance report generation from Prometheus API.
```

