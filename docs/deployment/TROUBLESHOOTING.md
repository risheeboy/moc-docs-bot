# Troubleshooting Guide

**Version:** 1.0.0
**Last Updated:** February 24, 2026

---

## Service Won't Start

### PostgreSQL fails to start

**Error:** `FATAL: could not create shared memory segment`

```bash
# 1. Check logs
docker-compose logs postgres | tail -20

# 2. Increase shared memory
sudo sysctl -w kernel.shmmax=17179869184
sudo sysctl -w kernel.shmall=4194304
echo "kernel.shmmax=17179869184" | sudo tee -a /etc/sysctl.conf
echo "kernel.shmall=4194304" | sudo tee -a /etc/sysctl.conf

# 3. Restart PostgreSQL
docker-compose restart postgres
```

### Redis fails to start

**Error:** `Address already in use`

```bash
# Find what's using port 6379
sudo lsof -i :6379

# Kill existing process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
# ports: ["6380:6379"]

docker-compose restart redis
```

### LLM service fails to load model

**Error:** `CUDA out of memory` or `Model loading timeout`

```bash
# 1. Check GPU memory
nvidia-smi

# 2. Free up GPU memory
docker-compose exec -T llm-service python -c \
    "import torch; torch.cuda.empty_cache()"

# 3. Reduce model size or memory utilization
# Edit .env:
LLM_MODEL_STANDARD=meta-llama/Llama-3.1-8B-Instruct-AWQ  # Use 8B instead of 13B
LLM_GPU_MEMORY_UTILIZATION=0.70  # Reduce from 0.85

# 4. Increase model loading timeout
# Edit docker-compose.yml:
# llm-service:
#   environment:
#     - VLLM_MODEL_LOADING_TIMEOUT_S=300  # from 180

docker-compose restart llm-service

# 5. Monitor loading
docker-compose logs -f llm-service | grep -i "model\|loaded\|cuda"
```

### Milvus fails to initialize

**Error:** `Failed to initialize Milvus or connect to etcd`

```bash
# 1. Check etcd (Milvus dependency)
docker-compose ps etcd

# 2. If etcd is down, start it first
docker-compose start etcd
sleep 5
docker-compose start milvus

# 3. If still failing, check volume permissions
ls -la /mnt/data/milvus-data
sudo chown -R 999:999 /mnt/data/milvus-data

# 4. Check etcd data isn't corrupted
docker-compose exec -T etcd etcdctl version
docker-compose exec -T etcd etcdctl member list

# 5. If corrupted, reset and restart
docker-compose down
rm -rf /mnt/data/etcd-data/*
docker-compose up -d etcd milvus
```

---

## Performance Issues

### API responses slow (>3 seconds)

```bash
# 1. Identify which endpoint is slow
# Check Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=http_request_duration_seconds&time=now' | jq '.data.result[0].value[1]'

# 2. Check individual service latency
curl -s http://localhost:8000/health | jq '.dependencies | keys[] as $k | "\($k): \(.[$k].latency_ms)ms"'

# 3. If RAG service slow:
#    - Check Milvus retrieval time
docker-compose logs rag-service | grep "retrieval_duration_ms" | tail -10

#    - Increase cache (cache hit rate)
docker-compose exec -T redis redis-cli INFO stats | grep hits

# 4. If LLM service slow:
#    - Reduce model size
#    - Increase GPU memory allocation
#    - Check GPU temperature (if >80C, thermal throttling)
nvidia-smi
```

### Chat endpoint timeout

**Error:** `504 Gateway Timeout`

```bash
# 1. Check if LLM service is responsive
curl -s http://localhost:8002/health

# 2. If LLM is stuck loading model:
docker-compose logs llm-service | tail -30

# 3. Increase timeout in nginx
# Edit nginx.conf:
# proxy_connect_timeout 30s;
# proxy_send_timeout 60s;
# proxy_read_timeout 120s;  # Increase from 60s

# 4. Reload nginx
docker-compose exec nginx nginx -s reload

# 5. Restart LLM service
docker-compose restart llm-service
```

### Memory leak in API gateway

**Error:** Container memory usage continuously increases

```bash
# 1. Check memory usage
docker stats api-gateway --no-stream

# 2. Check for connection leaks
docker-compose exec -T api-gateway python -c \
    "import psutil; p = psutil.Process(); print(f'Memory: {p.memory_info().rss/1e9:.2f}GB')"

# 3. Check database connection pool
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT count(*) FROM pg_stat_activity"

# 4. If too many connections (>30):
#    Restart API Gateway
docker-compose restart api-gateway

#    Or reduce connection pool in .env
SQLALCHEMY_POOL_SIZE=5  # from 10
SQLALCHEMY_POOL_RECYCLE=3600
```

---

## Database Issues

### PostgreSQL replication lag

**Error:** Data not visible in secondary database

```bash
# 1. Check replication status
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT * FROM pg_stat_replication"

# 2. If replication lagging:
#    - Check network between primary/secondary
#    - Check secondary storage space
#    - Check secondary CPU/memory

# 3. Resync replica
docker-compose exec -T postgres pg_basebackup -h primary -D /var/lib/postgresql/data -U replication
```

### Milvus search returns empty results

**Error:** Queries return no results despite documents being ingested

```bash
# 1. Verify collections exist
docker-compose exec -T milvus milvus_cli <<EOF
connect
show collections
exit
EOF

# 2. Verify embeddings exist
docker-compose exec -T milvus python3 -c \
    "from pymilvus import Collection; c=Collection('ministry_text'); print(f'Entities: {c.num_entities}')"

# 3. If no entities, trigger ingestion
curl -X POST http://localhost:8000/admin/ingestion/jobs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"target_urls": ["https://culture.gov.in"], "force_rescrape": true}'

# 4. If entities exist but search fails, check index
docker-compose exec -T milvus milvus_cli <<EOF
connect
collection_stats ministry_text
exit
EOF
```

---

## Network Issues

### Services can't communicate

**Error:** `Connection refused` between services

```bash
# 1. Check Docker network
docker network inspect rag-network

# 2. Verify service is running
docker-compose ps postgres
docker-compose ps api-gateway

# 3. Test DNS resolution
docker-compose exec api-gateway ping postgres
docker-compose exec api-gateway ping redis

# 4. If DNS fails, restart networking
docker-compose down
docker network rm rag-network
docker-compose up -d

# 5. Check firewall (if using UFW)
sudo ufw status
sudo ufw allow 19530/tcp  # Milvus
```

### SSL/TLS errors

**Error:** `certificate verify failed` or `SSL_ERROR_BAD_CERT_DOMAIN`

```bash
# 1. Check certificate expiry
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout | grep -A2 "Validity"

# 2. If expired, renew
sudo certbot renew --force-renewal

# 3. If self-signed (for testing only):
sudo openssl req -x509 -newkey rsa:4096 -nodes \
    -out /etc/nginx/ssl/cert.pem \
    -keyout /etc/nginx/ssl/key.pem \
    -days 365

# 4. Reload nginx
docker-compose restart nginx

# 5. Test
curl -k https://localhost/health  # -k ignores cert errors
```

---

## Data Issues

### Corrupted document embedding

**Error:** Search returns incorrect results for specific documents

```bash
# 1. Identify corrupted document
curl -X GET "http://localhost:8000/documents?page=1&page_size=100" \
    -H "Authorization: Bearer $TOKEN" | jq '.items[] | select(.title | contains("corrupted"))'

# 2. Delete and re-ingest
DOCUMENT_ID="550e8400-..."
curl -X DELETE "http://localhost:8000/documents/$DOCUMENT_ID" \
    -H "Authorization: Bearer $TOKEN"

# 3. Re-upload document
curl -X POST "http://localhost:8000/documents/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@document.pdf" \
    -F "title=Fixed Document"

# 4. Verify new embedding
sleep 30  # Wait for processing
curl -X GET "http://localhost:8000/documents/$NEW_ID" \
    -H "Authorization: Bearer $TOKEN"
```

### Session data lost

**Error:** User conversation history disappeared

```bash
# 1. Check Redis
docker-compose exec -T redis redis-cli
> GET session:session-id-here
> TTL session:session-id-here

# If TTL shows negative, session expired or deleted

# 2. Check PostgreSQL
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "SELECT * FROM conversations WHERE session_id='...'"

# 3. If in DB but not in Redis, restart API Gateway
docker-compose restart api-gateway

# 4. Configure longer timeout in .env
SESSION_IDLE_TIMEOUT_SECONDS=3600  # from 1800
```

---

## GPU Issues

### GPU not available in Docker

**Error:** `No GPUs available`

```bash
# 1. Check host GPU
nvidia-smi

# 2. Check NVIDIA Container Toolkit
which nvidia-container-runtime
nvidia-container-runtime --version

# 3. Verify docker-compose GPU specification
grep -A5 "services:" docker-compose.yml | grep -A2 "runtime: nvidia"

# 4. Test GPU in container
docker run --rm --runtime=nvidia --gpus all \
    nvidia/cuda:12.1.0-runtime-ubuntu22.04 \
    nvidia-smi

# 5. If fails, reinstall toolkit
sudo apt-get remove nvidia-container-toolkit
sudo apt-get install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### GPU temperature too high (>85°C)

**Error:** GPU throttling, slow performance

```bash
# 1. Check temperature
nvidia-smi --query-gpu=temperature.gpu,power.draw,power.limit --format=csv,noheader

# 2. Check thermal paste (physical inspection)
# Server should have good cooling

# 3. Reduce GPU load
#    - Reduce LLM_GPU_MEMORY_UTILIZATION
#    - Use smaller model
#    - Reduce concurrent requests (lower rate limit)

# 4. Increase cooling
#    - Improve server ventilation
#    - Clean cooling ducts/fans
#    - Lower server room temperature

# 5. Monitor
watch -n 1 "nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv,noheader"
```

---

## Debugging Techniques

### Enable verbose logging

```bash
# Edit .env
APP_LOG_LEVEL=DEBUG

# Restart services
docker-compose restart

# View logs
docker-compose logs api-gateway | head -100
```

### Attach to running container

```bash
# Interactive shell
docker-compose exec api-gateway bash

# Run Python commands
docker-compose exec api-gateway python -c "import sys; print(sys.version)"

# Check file contents
docker-compose exec api-gateway cat /app/config.json
```

### Monitor system calls

```bash
# Strace API gateway
docker-compose exec -T api-gateway strace -f -e trace=network python main.py 2>&1 | head -50
```

### Network packet capture

```bash
# Capture traffic between api-gateway and postgres
docker exec -it rag-qa-postgres tcpdump -i eth0 -nn host postgres

# Save to file
docker exec -it rag-qa-postgres \
    tcpdump -i eth0 -nn host postgres -w /tmp/capture.pcap

# Analyze
wireshark /tmp/capture.pcap
```

---

## Getting Help

### Collect diagnostic information

```bash
#!/bin/bash
# Create diagnostic bundle

OUTPUT="/tmp/rag-qa-diagnostics-$(date +%Y%m%d_%H%M%S).tar.gz"

mkdir -p /tmp/rag-qa-diag
cd /tmp/rag-qa-diag

# Collect logs
docker-compose logs > docker-compose.log 2>&1

# Collect configuration
cp /opt/rag-qa-hindi/.env .env.txt
docker-compose config > docker-compose.resolved.yml

# Collect system info
uname -a > system-info.txt
docker --version >> system-info.txt
nvidia-smi >> system-info.txt
df -h >> system-info.txt
free -h >> system-info.txt

# Collect metrics
curl -s http://localhost:9090/api/v1/series | jq . > prometheus-metrics.json
curl -s http://localhost:8000/health | jq . > api-health.json

# Create archive
cd ..
tar -czf $OUTPUT rag-qa-diag/

echo "Diagnostic bundle created: $OUTPUT"
echo "Send to: arit-culture@gov.in"
```

### Contact support

**Email:** arit-culture@gov.in
**Include:**
1. Diagnostic bundle (see above)
2. Error messages (full stack trace)
3. Steps to reproduce
4. Expected vs. actual behavior
5. Impact: how many users affected

---

**Last Updated:** February 24, 2026
