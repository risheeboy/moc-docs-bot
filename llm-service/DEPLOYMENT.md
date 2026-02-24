# LLM Service - Deployment Guide

## Overview

This guide covers deploying the LLM Service in Docker and Kubernetes environments.

## Prerequisites

- Docker 20.10+
- NVIDIA Docker runtime
- NVIDIA GPU with 48GB+ VRAM (recommended)
- CUDA 12.1+ driver installed
- HuggingFace account (for gated model access)

## Quick Deployment (Docker)

### 1. Build Image

```bash
cd llm-service
docker build -t llm-service:1.0.0 .
docker tag llm-service:1.0.0 llm-service:latest
```

### 2. Pre-download Models (Optional but Recommended)

```bash
# Create model cache directory
mkdir -p /mnt/models

# Download models to host volume
HF_HOME=/mnt/models bash model-download.sh
```

This pre-downloads ~80GB of model weights, eliminating startup delays.

### 3. Run Container

```bash
docker run -d \
  --name llm-service \
  --gpus all \
  -p 8002:8002 \
  -e LLM_LOAD_ON_STARTUP=true \
  -e LLM_PRELOAD_MODELS=standard,longctx \
  -e LLM_GPU_MEMORY_UTILIZATION=0.85 \
  -e LANGFUSE_ENABLED=true \
  -e LANGFUSE_HOST=http://langfuse:3001 \
  -e LANGFUSE_PUBLIC_KEY=pk_xxxxx \
  -e LANGFUSE_SECRET_KEY=sk_xxxxx \
  -v /mnt/models:/root/.cache/huggingface/hub \
  llm-service:1.0.0
```

### 4. Verify

```bash
# Check health
curl http://localhost:8002/health | jq

# View logs
docker logs -f llm-service

# Check GPU usage
docker exec llm-service nvidia-smi
```

## Docker Compose Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  llm-service:
    build: ./llm-service
    image: llm-service:1.0.0
    container_name: llm-service
    restart: unless-stopped
    ports:
      - "8002:8002"
    environment:
      - APP_ENV=production
      - APP_LOG_LEVEL=INFO
      - LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ
      - LLM_MODEL_LONGCTX=mistralai/Mistral-NeMo-Instruct-2407-AWQ
      - LLM_MODEL_MULTIMODAL=google/gemma-3-12b-it-awq
      - LLM_GPU_MEMORY_UTILIZATION=0.85
      - LLM_LOAD_ON_STARTUP=true
      - LLM_PRELOAD_MODELS=standard,longctx
      - LANGFUSE_ENABLED=true
      - LANGFUSE_HOST=http://langfuse:3001
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    volumes:
      - model-cache:/root/.cache/huggingface/hub
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    depends_on:
      - redis
      - langfuse

  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  langfuse:
    image: langfuse/langfuse:latest
    container_name: langfuse
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://langfuse_user:password@langfuse-postgres:5432/langfuse
    depends_on:
      - langfuse-postgres

  langfuse-postgres:
    image: postgres:16-alpine
    container_name: langfuse-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=langfuse_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-pg-data:/var/lib/postgresql/data

volumes:
  model-cache:
  redis-data:
  langfuse-pg-data:

networks:
  default:
    name: rag-network
    driver: bridge
```

Deploy:

```bash
docker-compose up -d
docker-compose logs -f llm-service
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace rag-system
```

### 2. Create ConfigMap for Environment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: llm-config
  namespace: rag-system
data:
  LLM_MODEL_STANDARD: "meta-llama/Llama-3.1-8B-Instruct-AWQ"
  LLM_MODEL_LONGCTX: "mistralai/Mistral-NeMo-Instruct-2407-AWQ"
  LLM_MODEL_MULTIMODAL: "google/gemma-3-12b-it-awq"
  LLM_GPU_MEMORY_UTILIZATION: "0.85"
  LLM_LOAD_ON_STARTUP: "true"
  LLM_PRELOAD_MODELS: "standard,longctx"
  APP_ENV: "production"
```

### 3. Create Secret for Langfuse

```bash
kubectl create secret generic langfuse-creds \
  --from-literal=public_key=pk_xxxxx \
  --from-literal=secret_key=sk_xxxxx \
  -n rag-system
```

### 4. Deploy Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: llm-service
  namespace: rag-system
spec:
  selector:
    app: llm-service
  type: ClusterIP
  ports:
    - port: 8002
      targetPort: 8002
      protocol: TCP
```

### 5. Deploy Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: llm-service
  namespace: rag-system
  labels:
    app: llm-service
spec:
  containers:
  - name: llm-service
    image: llm-service:1.0.0
    imagePullPolicy: IfNotPresent
    ports:
    - containerPort: 8002
      name: http
    envFrom:
    - configMapRef:
        name: llm-config
    env:
    - name: LANGFUSE_PUBLIC_KEY
      valueFrom:
        secretKeyRef:
          name: langfuse-creds
          key: public_key
    - name: LANGFUSE_SECRET_KEY
      valueFrom:
        secretKeyRef:
          name: langfuse-creds
          key: secret_key
    resources:
      requests:
        nvidia.com/gpu: 1
        memory: "24Gi"
        cpu: "4"
      limits:
        nvidia.com/gpu: 1
        memory: "48Gi"
        cpu: "8"
    livenessProbe:
      httpGet:
        path: /health
        port: 8002
      initialDelaySeconds: 60
      periodSeconds: 30
      timeoutSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health
        port: 8002
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    volumeMounts:
    - name: model-cache
      mountPath: /root/.cache/huggingface/hub
  volumes:
  - name: model-cache
    emptyDir: {}
  restartPolicy: Always
```

Deploy:

```bash
kubectl apply -f llm-service-config.yaml
kubectl apply -f llm-service-secret.yaml
kubectl apply -f llm-service-service.yaml
kubectl apply -f llm-service-pod.yaml

# Check status
kubectl get pods -n rag-system
kubectl logs -f llm-service -n rag-system
```

## GPU Configuration

### Single GPU Scenarios

#### 24GB GPU (RTX 3090)
```bash
LLM_GPU_MEMORY_UTILIZATION=0.75
LLM_PRELOAD_MODELS=standard  # Load only standard model
```

#### 48GB GPU (A6000)
```bash
LLM_GPU_MEMORY_UTILIZATION=0.85
LLM_PRELOAD_MODELS=standard,longctx  # Load two models
```

#### 80GB GPU (A100)
```bash
LLM_GPU_MEMORY_UTILIZATION=0.90
LLM_PRELOAD_MODELS=standard,longctx,multimodal  # Load all models
```

### Multi-GPU Setup

For distributed inference (future enhancement):

```bash
LLM_TENSOR_PARALLEL_SIZE=2  # 2 GPUs
# Models will be split across GPUs
```

## Monitoring & Logs

### Access Logs

Docker:
```bash
docker logs -f llm-service
docker logs llm-service --tail 100
```

Kubernetes:
```bash
kubectl logs -f llm-service -n rag-system
kubectl logs llm-service --tail 100 -n rag-system
```

### Metrics

Prometheus endpoint: http://localhost:8002/metrics

Key metrics:
```
llm_tokens_generated_total{model="..."}
llm_inference_duration_seconds{model="..."}
llm_model_loaded{model="..."}
llm_requests_total{model="...", status="success"}
```

### Health Check

```bash
# Container health
curl http://localhost:8002/health

# Model status
curl http://localhost:8002/health | jq .dependencies
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs llm-service

# Common issues:
# - GPU not available: docker run --gpus all
# - Insufficient memory: increase host memory
# - Model download timeout: pre-download models
```

### Out of Memory

```bash
# Reduce GPU memory usage
docker update --env LLM_GPU_MEMORY_UTILIZATION=0.7 llm-service

# Or reduce context length
docker update --env LLM_MAX_MODEL_LEN_STANDARD=4096 llm-service

# Restart
docker restart llm-service
```

### High Latency

```bash
# Check GPU utilization
nvidia-smi

# Check inference metrics
curl http://localhost:8002/metrics | grep duration

# Reduce concurrent requests or increase GPU memory
```

### Model Loading Timeout

```bash
# Increase startup grace period
# Docker: increase healthcheck start_period
# Kubernetes: increase initialDelaySeconds

# Or pre-download models before deployment
```

## Production Checklist

- [ ] GPUs available and properly configured
- [ ] Models pre-downloaded to persistent volume
- [ ] Langfuse credentials configured
- [ ] Redis for caching available
- [ ] Memory and CPU limits set appropriately
- [ ] Health checks configured
- [ ] Monitoring/logging configured
- [ ] Secrets stored securely (not in env vars)
- [ ] Regular backup of model cache
- [ ] Load testing completed

## Performance Tuning

### Optimize for Throughput

```bash
LLM_GPU_MEMORY_UTILIZATION=0.90  # Max GPU usage
LLM_PRELOAD_MODELS=standard      # Single model
# Use smaller batch sizes in client
```

### Optimize for Latency

```bash
LLM_GPU_MEMORY_UTILIZATION=0.70  # Lower memory pressure
# Pre-warm models before traffic
# Use dedicated GPU
```

### Optimize for Memory

```bash
LLM_GPU_MEMORY_UTILIZATION=0.60
LLM_PRELOAD_MODELS=standard
LLM_MAX_MODEL_LEN_STANDARD=4096
```

## Scaling Strategy

1. **Single GPU**: Load model on-demand, unload after use
2. **Multi-GPU**: Tensor parallel for large models
3. **Multiple Machines**: Deploy multiple instances, use load balancer

## Backup & Recovery

### Backup Models

```bash
# Backup model cache
docker cp llm-service:/root/.cache/huggingface/hub ./backup/

# Or use volume backup
docker cp llm-service:/root/.cache/huggingface/hub /mnt/backup/
```

### Recovery

```bash
# Restore from backup
docker cp ./backup/hub llm-service:/root/.cache/huggingface/
docker restart llm-service
```

## Related Documents

- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Implementation details
