# Translation Service - Deployment Guide

## Quick Start

### Prerequisites
- Docker with NVIDIA Container Toolkit (for GPU support)
- CUDA 12.1+ and cuDNN 8.9+
- Python 3.11 (for local development)
- Redis 7+ (running on `redis:6379`)

### Environment Setup

Create a `.env` file in the translation-service directory:

```bash
# Application
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Translation Service
TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B
TRANSLATION_CACHE_TTL_SECONDS=86400
TRANSLATION_BATCH_SIZE=32
TRANSLATION_MAX_BATCH_ITEMS=100
TRANSLATION_TIMEOUT_SECONDS=60

# Redis (must match main system)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_redis_password
REDIS_DB_TRANSLATION=3

# Model Cache
MODEL_CACHE_DIR=/root/.cache/huggingface/hub
```

## Docker Build & Run

### Build the image
```bash
cd translation-service
docker build -t translation-service:1.0.0 .
```

This will:
1. Install Python 3.11 and system dependencies
2. Install Python packages from requirements.txt
3. Download and cache IndicTrans2 model weights
4. Build the final image (~8-10GB with models)

### Run locally with Docker
```bash
docker run -d \
  --name translation-service \
  --network rag-network \
  --env-file .env \
  -v model-cache:/root/.cache/huggingface/hub \
  --gpus all \
  -p 8004:8004 \
  translation-service:1.0.0
```

### Verify service is running
```bash
curl -X GET http://localhost:8004/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "translation-service",
  "version": "1.0.0",
  "uptime_seconds": 15,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "redis": {"status": "healthy", "latency_ms": 2},
    "gpu_model": {"status": "healthy", "latency_ms": 45}
  }
}
```

## Docker Compose Integration

Add to the main `docker-compose.yml`:

```yaml
services:
  translation-service:
    build:
      context: ./translation-service
      dockerfile: Dockerfile
    container_name: translation-service
    ports:
      - "8004:8004"
    environment:
      - APP_ENV=${APP_ENV:-production}
      - APP_DEBUG=${APP_DEBUG:-false}
      - APP_LOG_LEVEL=${APP_LOG_LEVEL:-INFO}
      - TRANSLATION_MODEL=${TRANSLATION_MODEL:-ai4bharat/indictrans2-indic-en-1B}
      - TRANSLATION_CACHE_TTL_SECONDS=${TRANSLATION_CACHE_TTL_SECONDS:-86400}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_DB_TRANSLATION=3
      - MODEL_CACHE_DIR=/root/.cache/huggingface/hub
    volumes:
      - model-cache:/root/.cache/huggingface/hub
    networks:
      - rag-network
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    restart: unless-stopped
    labels:
      - "com.ragqa.service=translation-service"
      - "com.ragqa.version=1.0.0"
      - "com.ragqa.stream=13"
```

## Local Development

### Setup virtual environment
```bash
cd translation-service
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx  # For testing
```

### Run tests
```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Run locally without Docker
```bash
# Make sure Redis is running
# Then start the service:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## Testing the Service

### Single Translation
```bash
curl -X POST http://localhost:8004/translate \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -d '{
    "text": "Ministry of Culture",
    "source_language": "en",
    "target_language": "hi"
  }'
```

### Batch Translation
```bash
curl -X POST http://localhost:8004/translate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World", "India"],
    "source_language": "en",
    "target_language": "hi"
  }'
```

### Language Detection
```bash
curl -X POST http://localhost:8004/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "यह हिंदी में लिखा गया है"}'
```

### Health Check
```bash
curl http://localhost:8004/health
```

### Metrics
```bash
curl http://localhost:8004/metrics
```

## Kubernetes Deployment

### Create ConfigMap and Secret
```bash
kubectl create configmap translation-config \
  --from-literal=APP_ENV=production \
  --from-literal=APP_LOG_LEVEL=INFO \
  --from-literal=TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B

kubectl create secret generic translation-secret \
  --from-literal=REDIS_PASSWORD=<secure-password>
```

### Apply Kubernetes manifests

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: translation-service
  labels:
    app: translation-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: translation-service
  template:
    metadata:
      labels:
        app: translation-service
    spec:
      containers:
      - name: translation-service
        image: translation-service:1.0.0
        ports:
        - containerPort: 8004
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: translation-config
              key: APP_ENV
        - name: REDIS_HOST
          value: redis
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: translation-secret
              key: REDIS_PASSWORD
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: 1
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 120
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 60
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: translation-service
spec:
  selector:
    app: translation-service
  ports:
  - protocol: TCP
    port: 8004
    targetPort: 8004
  type: ClusterIP
```

## Troubleshooting

### Service won't start - Model download failing
```bash
# Pre-download model manually
python3 << 'EOF'
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model_name = "ai4bharat/indictrans2-indic-en-1B"
print("Downloading tokenizer...")
AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
print("Downloading model...")
AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
print("Done!")
EOF
```

### GPU not detected
```bash
# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi

# Check container has GPU access
docker run --rm --gpus all translation-service:1.0.0 python3 -c "import torch; print(torch.cuda.is_available())"
```

### Redis connection failures
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli -h redis -p 6379 ping
# Should return: PONG
```

### Translation timeout
```bash
# Check service logs
docker logs translation-service

# Check model is loaded
curl http://localhost:8004/health | jq '.dependencies.gpu_model'
```

## Performance Tuning

### For faster inference
1. Reduce beam search: Modify `beam_search` parameter in `indictrans2_engine.py`
2. Increase batch size: Adjust `TRANSLATION_BATCH_SIZE` in config
3. Use quantized models: Replace with AWQ or GPTQ variants

### For lower GPU memory
1. Use smaller model: `ai4bharat/indictrans2-indic-en-256M`
2. Enable gradient checkpointing
3. Reduce max_length in inference

### For better cache hit rate
1. Increase `TRANSLATION_CACHE_TTL_SECONDS`
2. Monitor cache stats via `/metrics`
3. Pre-populate cache with common translations

## Monitoring

### Prometheus scrape config
```yaml
scrape_configs:
  - job_name: 'translation-service'
    static_configs:
      - targets: ['translation-service:8004']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Key metrics to monitor
```
translation_duration_seconds - Translation latency
translation_cache_hit_total - Cache effectiveness
gpu_model_loaded - Model health
http_requests_total - Request volume
```

## Logs Location

Logs are output to stdout in JSON format:

```bash
# View logs
docker logs translation-service

# Grep for errors
docker logs translation-service | grep '"level":"ERROR"'

# Parse with jq
docker logs translation-service | jq '.level,.message'
```

## Security Considerations

1. **API Key Protection:** Ensure API Gateway implements authentication
2. **HTTPS Only:** Use NGINX reverse proxy with TLS
3. **Rate Limiting:** Configured in API Gateway (§3 Shared Contracts)
4. **PII Logging:** Service never logs full text of user queries
5. **Model Updates:** Verify model source before building

## Backup & Recovery

### Backup cache
```bash
docker exec redis redis-cli -n 3 BGSAVE
docker cp redis:/data/dump.rdb ./backup/
```

### Clear cache if needed
```bash
docker exec redis redis-cli -n 3 FLUSHDB
```

## Version Updates

To update to a new model or service version:

```bash
# 1. Update TRANSLATION_MODEL in .env
TRANSLATION_MODEL=ai4bharat/indictrans2-indic-en-1B-v2

# 2. Rebuild image
docker build -t translation-service:1.0.1 .

# 3. Update docker-compose or k8s manifests
# 4. Restart service
docker-compose up -d translation-service
```

---

**Last Updated:** 2026-02-24
**Maintained by:** RAG QA System Team
