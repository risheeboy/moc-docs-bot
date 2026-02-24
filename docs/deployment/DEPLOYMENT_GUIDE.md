# Deployment Guide — NIC/MeitY Data Centre

**Version:** 1.0.0
**Target Environment:** Production (NIC/MeitY Data Centre)
**Last Updated:** February 24, 2026

---

## Table of Contents

1. [Pre-Deployment](#pre-deployment)
2. [System Preparation](#system-preparation)
3. [Clone & Configure](#clone--configure)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Service Initialization](#service-initialization)
6. [Verification & Testing](#verification--testing)
7. [Post-Deployment Tasks](#post-deployment-tasks)
8. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment

### Prerequisites Checklist

Complete all items in [PREREQUISITES.md](PREREQUISITES.md):

- [ ] OS: Ubuntu 22.04 LTS
- [ ] GPU: NVIDIA A100 or equivalent (check: `nvidia-smi`)
- [ ] Driver: version 535+ (check: `nvidia-driver --version`)
- [ ] CUDA: 12.1+ (check: `nvcc --version`)
- [ ] Docker: 27.x+ (check: `docker --version`)
- [ ] NVIDIA Container Toolkit (check: `docker run --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi`)
- [ ] Storage: 500GB SSD + 10TB HDD configured
- [ ] Network: 10 Gbps connection verified

### Create Deployment User

```bash
# Create non-root user for running services
sudo useradd -m -s /bin/bash -G docker ragqa

# Set password
sudo passwd ragqa

# Switch to deployment user
sudo su - ragqa
```

### Set Working Directory

```bash
# Create deployment directory
mkdir -p /opt/rag-qa-hindi
cd /opt/rag-qa-hindi

# Ensure ownership
sudo chown ragqa:ragqa /opt/rag-qa-hindi
chmod 755 /opt/rag-qa-hindi
```

---

## System Preparation

### 1. Network Configuration

```bash
# Verify network connectivity
ping -c 1 8.8.8.8

# Check DNS
nslookup culture.gov.in

# Verify firewall rules (adjust as needed)
sudo ufw status

# Allow required ports (if using UFW)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 22/tcp   # SSH
```

### 2. Storage Preparation

```bash
# Create storage directories
mkdir -p /mnt/data/documents
mkdir -p /mnt/data/models
mkdir -p /mnt/backup

# Set permissions
sudo chown -R ragqa:ragqa /mnt/data /mnt/backup
chmod -R 755 /mnt/data /mnt/backup

# Check space
df -h /mnt/data /mnt/backup
```

### 3. SSL Certificate Setup

Obtain TLS certificate for `culture.gov.in`:

**Option A: Let's Encrypt (free, automated)**

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone \
    -d culture.gov.in \
    -d www.culture.gov.in

# Certificate path: /etc/letsencrypt/live/culture.gov.in/
```

**Option B: NIC-provided certificate**

```bash
# Copy certificate and key from NIC
sudo cp /path/to/cert.pem /etc/nginx/ssl/cert.pem
sudo cp /path/to/key.pem /etc/nginx/ssl/key.pem

# Set permissions
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chmod 644 /etc/nginx/ssl/cert.pem
```

### 4. Docker Network Creation

```bash
# Create Docker bridge network
docker network create rag-network --driver bridge

# Verify
docker network ls | grep rag-network
```

---

## Clone & Configure

### 1. Clone Repository

```bash
cd /opt/rag-qa-hindi

# Clone from NIC's GitLab/GitHub (or local copy)
git clone https://gitlab.nic.in/rag-qa-hindi.git .

# Or if using local archive
unzip rag-qa-hindi.zip

# Verify structure
ls -la
# Expected: docker-compose.yml, .env.example, docs/, etc.
```

### 2. Create Environment File

```bash
# Copy example configuration
cp .env.example .env

# Edit with production values
nano .env
```

**Critical Variables (update from CONFIGURATION.md):**

```bash
# App settings
APP_ENV=production
APP_DEBUG=false
APP_SECRET_KEY=<generate-new-256-bit-hex>

# Database passwords (generate strong values)
POSTGRES_PASSWORD=<strong-password>
LANGFUSE_PG_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
MINIO_SECRET_KEY=<strong-password>

# JWT secret
JWT_SECRET_KEY=<generate-new-256-bit-hex>

# SSL paths
NGINX_SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
NGINX_SSL_KEY_PATH=/etc/nginx/ssl/key.pem
NGINX_DOMAIN=culture.gov.in

# LLM model settings (adjust for your GPU)
LLM_GPU_MEMORY_UTILIZATION=0.85  # Reduce to 0.70 if OOM errors

# Langfuse credentials (get from Langfuse setup)
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxx
```

### 3. Prepare Docker Compose File

```bash
# Verify docker-compose.yml exists
cat docker-compose.yml | head -20

# Check for placeholder values
grep -n "CHANGEME\|TODO\|FIXME" docker-compose.yml
```

### 4. Prepare Volumes

```bash
# Create named volumes
docker volume create postgres-data
docker volume create langfuse-pg-data
docker volume create milvus-data
docker volume create etcd-data
docker volume create redis-data
docker volume create minio-data
docker volume create model-cache
docker volume create uploaded-docs
docker volume create backup-data
docker volume create loki-data

# Verify
docker volume ls | grep -E "postgres|milvus|redis|minio|model|backup|loki"
```

### 5. Copy SSL Certificates to Container Mount

```bash
# Create SSL directory for Docker bind mount
sudo mkdir -p /etc/nginx/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/culture.gov.in/fullchain.pem /etc/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/culture.gov.in/privkey.pem /etc/nginx/ssl/key.pem

# Set restrictive permissions
sudo chmod 600 /etc/nginx/ssl/key.pem
sudo chmod 644 /etc/nginx/ssl/cert.pem

# Verify NGINX can read
sudo chown -R 101:101 /etc/nginx/ssl  # NGINX UID:GID in official image
```

---

## Docker Compose Deployment

### 1. Start Services (Sequential)

```bash
# Change to deployment directory
cd /opt/rag-qa-hindi

# Pull latest images
docker-compose pull

# Start services in order
# First, start databases (these must be ready before API services)

# Start PostgreSQL, Redis, Milvus
docker-compose up -d postgres redis milvus etcd

# Wait for databases to be healthy (2-3 minutes)
sleep 30
docker-compose ps

# Check PostgreSQL is running
docker-compose logs postgres | tail -20
```

### 2. Initialize Databases

```bash
# PostgreSQL initialization
docker-compose exec -T postgres psql -U ragqa_user -d ragqa -c "\dt"

# Create initial schema (run migrations)
docker-compose exec -T api-gateway alembic upgrade head

# MinIO bucket creation
docker-compose exec -T minio mc alias set minio http://localhost:9000 minioadmin $MINIO_SECRET_KEY
docker-compose exec -T minio mc mb minio/documents minio/models minio/backups
```

### 3. Start Core Services

```bash
# Start object storage and cache
docker-compose up -d minio

# Wait for MinIO to be ready
sleep 10

# Start backend services
docker-compose up -d \
    llm-service \
    rag-service \
    speech-service \
    translation-service \
    ocr-service \
    api-gateway

# Wait for services to initialize (3-5 minutes for model downloads)
sleep 60
docker-compose logs api-gateway | tail -30
```

### 4. Start Frontend & Monitoring

```bash
# Start frontend SPAs
docker-compose up -d \
    chat-widget \
    search-page \
    admin-dashboard

# Start monitoring
docker-compose up -d \
    prometheus \
    grafana \
    langfuse

# Start NGINX
docker-compose up -d nginx

# Check all services
docker-compose ps
```

### 5. Verify Service Health

```bash
# All services should be "Up"
docker-compose ps

# Expected output:
# NAME                    STATUS
# postgres                Up (healthy)
# redis                   Up
# milvus                  Up (healthy)
# api-gateway             Up (healthy)
# llm-service             Up (healthy)
# rag-service             Up (healthy)
# chat-widget             Up
# search-page             Up
# admin-dashboard         Up
# nginx                   Up
# prometheus              Up
# grafana                 Up
# langfuse                Up
```

---

## Service Initialization

### 1. Wait for Model Downloads

LLM models (Llama 3.1, Mistral NeMo, Gemma) download on first startup (~10-15 minutes):

```bash
# Monitor LLM service logs
docker-compose logs -f llm-service

# Watch for message:
# "Served model meta-llama/Llama-3.1-8B-Instruct-AWQ"
# "Model is loaded in memory"

# Check GPU memory usage
nvidia-smi

# Should show:
# GPU 0: ~40-50 GB used (varies by model and quantization)
```

### 2. Initialize Vector Database

```bash
# Verify Milvus collections exist
docker-compose exec -T milvus python -c \
    "from pymilvus import Collection; Collection('ministry_text')"

# If collections don't exist, trigger initial ingestion:
curl -X POST http://localhost:8000/admin/ingestion/jobs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "target_urls": ["https://culture.gov.in"],
        "spider_type": "auto",
        "force_rescrape": false
    }'
```

### 3. Create Admin User

```bash
# Access API Gateway container
docker-compose exec api-gateway bash

# Run user creation script
python scripts/create_admin_user.py \
    --email admin@culture.gov.in \
    --password <strong-password> \
    --role admin

# Exit container
exit
```

### 4. Initialize Langfuse

```bash
# Access Langfuse
curl http://localhost:3001

# If first-time setup:
# 1. Open http://culture.gov.in/langfuse in browser
# 2. Create account and workspace
# 3. Generate API keys
# 4. Update LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env
# 5. Restart services: docker-compose restart
```

---

## Verification & Testing

### 1. Health Checks

```bash
# API Gateway health
curl -s http://localhost:8000/health | jq .

# Expected response:
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "dependencies": {
    "postgres": { "status": "healthy" },
    "redis": { "status": "healthy" },
    "milvus": { "status": "healthy" },
    "llm_service": { "status": "healthy" }
  }
}
```

### 2. Test Chat Endpoint

```bash
# Get admin token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@culture.gov.in",
        "password": "<password>"
    }' | jq -r .access_token)

# Test chat
curl -X POST http://localhost:8000/api/v1/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "नमस्ते",
        "language": "hi"
    }' | jq .

# Expected: Response with sources and confidence score
```

### 3. Test Search Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/search \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "heritage sites",
        "language": "en",
        "page": 1,
        "page_size": 10
    }' | jq .
```

### 4. Test Voice Services

```bash
# STT (requires audio file)
curl -X POST http://localhost:8000/api/v1/voice/stt \
    -H "Authorization: Bearer $TOKEN" \
    -F "audio=@test.wav" \
    -F "language=hi"

# TTS
curl -X POST http://localhost:8000/api/v1/voice/tts \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "नमस्ते दुनिया",
        "language": "hi",
        "format": "mp3"
    }' --output response.mp3
```

### 5. Frontend Access

```bash
# Chat Widget
curl -I https://culture.gov.in/chat-widget

# Search Page
curl -I https://culture.gov.in/search

# Admin Dashboard
curl -I https://culture.gov.in/admin

# All should return 200 OK
```

### 6. Monitor Logs

```bash
# View logs for specific service
docker-compose logs -f api-gateway

# View all logs
docker-compose logs -f --tail=100

# Search for errors
docker-compose logs | grep ERROR

# Export logs to file
docker-compose logs > deployment.log 2>&1
```

---

## Post-Deployment Tasks

### 1. Enable Auto-Restart

```bash
# Set all services to restart automatically
docker-compose up -d --restart-policy unless-stopped
```

### 2. Configure Regular Backups

```bash
# Create backup script (see BACKUP_RESTORE.md)
# Schedule daily backups at 2 AM
crontab -e

# Add line:
0 2 * * * /opt/rag-qa-hindi/scripts/backup.sh
```

### 3. Setup Monitoring Alerts

```bash
# Configure Prometheus alerts (update prometheus.yml)
# Example alert: API response time > 5s

# Access Grafana
# http://culture.gov.in/grafana
# Default credentials: admin/admin

# Import dashboard: "RAG-QA System Monitoring"
# Create alerts: HTTP latency, GPU memory, disk space
```

### 4. Configure Log Rotation

```bash
# Setup Loki for log aggregation
# Logs accessible via Grafana Explore

# Configure retention policy in .env:
RETENTION_CONVERSATIONS_DAYS=90
RETENTION_AUDIT_LOG_DAYS=730
```

### 5. Document Current Configuration

```bash
# Export configuration snapshot
docker-compose config > docker-compose.prod.yml

# Save .env securely (for disaster recovery)
sudo cp .env /mnt/backup/.env.backup
sudo chmod 600 /mnt/backup/.env.backup

# Document deployment details
cat > DEPLOYMENT_NOTES.txt <<EOF
Deployment Date: $(date)
System: $(uname -a)
GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)
CUDA: $(nvcc --version | grep release)
Docker: $(docker --version)
Deployed Services: $(docker-compose ps --services)
EOF
```

---

## Rollback Procedures

### Scenario 1: Critical Service Failure

```bash
# Stop all services
docker-compose down

# Check logs for error
docker-compose logs api-gateway | tail -50

# Restart single service
docker-compose up -d api-gateway

# Monitor
docker-compose logs -f api-gateway
```

### Scenario 2: Configuration Error

```bash
# Revert .env to backup
sudo cp /mnt/backup/.env.backup .env

# Restart services
docker-compose down
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

### Scenario 3: Data Corruption

```bash
# Stop services
docker-compose down

# Restore from backup (see BACKUP_RESTORE.md)
./scripts/restore.sh /mnt/backup/latest

# Restart
docker-compose up -d

# Verify
docker-compose exec -T postgres psql -U ragqa_user -d ragqa -c "SELECT count(*) FROM documents"
```

### Scenario 4: Full System Restore

```bash
# If disaster recovery needed, follow DISASTER_RECOVERY.md
# Time estimate: 1-4 hours depending on data size
```

---

## Performance Tuning

### GPU Memory Optimization

```bash
# If experiencing OOM errors:

# 1. Reduce GPU memory utilization
LLM_GPU_MEMORY_UTILIZATION=0.70

# 2. Use smaller model
LLM_MODEL_STANDARD=mistral-7b  # Instead of 13b

# 3. Restart service
docker-compose restart llm-service
```

### CPU & Memory Optimization

```bash
# Monitor resource usage
docker stats

# Set resource limits in docker-compose.yml:
services:
  api-gateway:
    resources:
      limits:
        cpus: "8.0"
        memory: 16G
      reservations:
        cpus: "4.0"
        memory: 8G
```

### Query Performance

```bash
# Enable query caching (default RAG_CACHE_TTL_SECONDS=3600)
# Check cache hit rate:
curl http://localhost:8000/metrics | grep rag_cache_hit

# Index Milvus collections
docker-compose exec -T milvus milvus_cli
# > collection_stats
# > index_list
```

---

## Troubleshooting

### Services fail to start

```bash
# Check disk space
df -h

# Check Docker images exist
docker images | grep rag-qa

# Check .env syntax
grep -E "^[A-Z_]+=" .env | wc -l
```

### GPU not available in containers

```bash
# Verify NVIDIA Container Toolkit
which nvidia-container-runtime

# Test GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# Reinstall if needed
sudo apt-get remove nvidia-container-toolkit
sudo apt-get install nvidia-container-toolkit
```

### Port conflicts

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill if necessary
sudo kill -9 <PID>

# Or change port in docker-compose.yml and .env
```

### Database connection refused

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec -T postgres psql -U ragqa_user -d ragqa -c "SELECT 1"

# If fails, check logs
docker-compose logs postgres
```

---

## Summary

Deployment checklist:
- [ ] Prerequisites verified
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Docker volumes created
- [ ] Services started in order
- [ ] All health checks passing
- [ ] Admin user created
- [ ] Test endpoints working
- [ ] Backups scheduled
- [ ] Monitoring configured
- [ ] Documentation updated

**Deployment Time:** 30-45 minutes (excluding initial model downloads which take 10-15 minutes)

**Next Steps:**
- Monitor system for 24 hours
- Configure auto-scaling (if applicable)
- Setup incident response procedures
- Train operations team

---

**Support:** For deployment issues, contact arit-culture@gov.in

**Last Updated:** February 24, 2026
