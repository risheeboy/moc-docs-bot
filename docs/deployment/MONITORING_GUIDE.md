# Monitoring Guide

**Version:** 1.0.0
**Tools:** Prometheus, Grafana, Langfuse
**Last Updated:** February 24, 2026

---

## Quick Start

```bash
# Access monitoring dashboards
Grafana:   http://culture.gov.in/grafana (admin/admin)
Prometheus: http://culture.gov.in/prometheus
Langfuse:  http://culture.gov.in/langfuse
```

---

## Prometheus Metrics

### Key Metrics to Monitor

```
# API Gateway
http_requests_total                    # Total requests by endpoint/status
http_request_duration_seconds          # Response latency histogram
rate_limit_exceeded_total              # Rate limit violations

# LLM Service
llm_tokens_generated_total             # Tokens produced (billing metric)
llm_inference_duration_seconds         # LLM response time
llm_model_loaded                       # Model loaded state (gauge)

# RAG Service
rag_retrieval_duration_seconds         # Document retrieval time
rag_cache_hit_total                    # Cache hits (should be >70%)
rag_cache_miss_total                   # Cache misses

# Speech
speech_stt_duration_seconds            # Speech-to-text latency
speech_tts_duration_seconds            # Text-to-speech latency

# Translation
translation_duration_seconds           # Translation latency
translation_cache_hit_total            # Should be >80%

# Data Ingestion
ingestion_pages_crawled_total          # Pages processed
ingestion_documents_ingested_total     # Documents ingested
ingestion_errors_total                 # Scraping errors

# System
gpu_memory_used                        # GPU memory in use (bytes)
gpu_temperature_celsius                # GPU temperature
disk_free_bytes                        # Free disk space
```

### Prometheus Queries

```
# API latency (95th percentile)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error rate (last 5 minutes)
rate(http_requests_total{status=~"5.."}[5m])

# Cache hit rate
rate(rag_cache_hit_total[5m]) / (rate(rag_cache_hit_total[5m]) + rate(rag_cache_miss_total[5m]))

# GPU utilization
gpu_memory_used / gpu_memory_total

# Document ingestion rate
rate(ingestion_documents_ingested_total[1h])
```

---

## Grafana Dashboards

### Import Pre-built Dashboards

```bash
# 1. Login to Grafana: http://culture.gov.in/grafana
# 2. Click "+" → "Import"
# 3. Paste dashboard ID or JSON

# Recommended dashboards:
# - 1860: Node Exporter (system metrics)
# - 8919: Prometheus (Prometheus internals)
# - Custom: "RAG-QA System Overview"
```

### Create Custom Dashboard

**RAG-QA System Overview:**

| Panel | Metric | Threshold |
|---|---|---|
| API Latency (p95) | http_request_duration_seconds | <2000ms |
| Error Rate | rate(errors[5m]) | <0.5% |
| Cache Hit Rate | cache_hit / (cache_hit + cache_miss) | >70% |
| GPU Memory | gpu_memory_used / total | <90% |
| Disk Free | disk_free_bytes | >500GB |
| Chat Response Time | rag_retrieval_duration + llm_inference_duration | <5000ms |

---

## Alert Rules

### Critical Alerts

```yaml
groups:
- name: rag-qa-critical
  interval: 30s
  rules:

  # API Gateway down
  - alert: APIGatewayDown
    expr: up{job="api-gateway"} == 0
    for: 2m
    annotations:
      summary: "API Gateway is down"
      action: "Restart: docker-compose restart api-gateway"

  # Database down
  - alert: PostgreSQLDown
    expr: up{job="postgres"} == 0
    for: 2m
    annotations:
      summary: "PostgreSQL is unreachable"
      action: "Check: docker-compose logs postgres"

  # GPU memory critical
  - alert: GPUMemoryCritical
    expr: gpu_memory_used / gpu_memory_total > 0.95
    for: 5m
    annotations:
      summary: "GPU memory >95% - may cause OOM"
      action: "Reduce gpu_memory_utilization in .env"

  # Disk space low
  - alert: DiskSpaceLow
    expr: disk_free_bytes < 50_000_000_000  # <50GB
    for: 5m
    annotations:
      summary: "Free disk space <50GB"
      action: "Run cleanup: ./scripts/cleanup.sh"

  # High error rate
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "Error rate >5%"
      action: "Check logs: docker-compose logs api-gateway"
```

### Configure Alert Notifications

```yaml
# In prometheus.yml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# In alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

route:
  receiver: 'ops-alerts'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'ops-alerts'
    slack_configs:
      - channel: '#ops-alerts'
        title: 'RAG-QA Alert'
        text: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
```

---

## Langfuse for LLM Observability

### Cost Tracking

```python
# Every LLM call is tracked:
from langfuse import Langfuse

langfuse = Langfuse()

# LLM call
response = llm.generate(prompt)

# Cost calculated automatically:
# Input tokens: $0.001 per 1K tokens (Llama)
# Output tokens: $0.002 per 1K tokens
# Cost = (input_tokens * 0.001 + output_tokens * 0.002) / 1000
```

### Usage Metrics

```
Access: http://culture.gov.in/langfuse → Dashboard

Metrics shown:
- Total tokens per day (tracked for billing)
- Cost per model variant
- Latency distribution
- Error rate
- User feedback correlation with cost
```

### Trace Analysis

```
1. View recent traces: Langfuse dashboard
2. Identify slow traces (>3s latency)
3. Drill into trace to see:
   - RAG retrieval time
   - LLM inference time
   - Post-processing time
4. Optimize bottlenecks
```

---

## Health Check Endpoints

### API Gateway Health

```bash
curl -s http://localhost:8000/health | jq .
```

Response:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "version": "1.0.0",
  "uptime_seconds": 36000,
  "timestamp": "2026-02-24T12:00:00Z",
  "dependencies": {
    "postgres": { "status": "healthy", "latency_ms": 5 },
    "redis": { "status": "healthy", "latency_ms": 2 },
    "milvus": { "status": "healthy", "latency_ms": 12 },
    "llm_service": { "status": "healthy", "latency_ms": 1200 }
  }
}
```

Status Values:
- `healthy`: All dependencies operational
- `degraded`: Some non-critical deps down (cache, non-essential services)
- `unhealthy`: Critical dependency failed (returns HTTP 503)

---

## Daily Operations

### Morning Checks (9 AM)

```bash
#!/bin/bash
# Daily health check script

echo "=== RAG-QA Daily Health Check ==="
echo "Time: $(date)"

# 1. All services running
echo -e "\n1. Service Status:"
docker-compose ps | grep -E "STATUS|Up"

# 2. Recent errors
echo -e "\n2. Recent Errors:"
docker-compose logs --since 24h | grep ERROR | tail -5

# 3. Resource usage
echo -e "\n3. Resource Usage:"
docker stats --no-stream | head -10

# 4. GPU status
echo -e "\n4. GPU Status:"
nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader

# 5. Backup status
echo -e "\n5. Backup Status:"
ls -lht /mnt/backup/postgres | head -3

# 6. API response
echo -e "\n6. API Response:"
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
    -X GET http://localhost:8000/health | jq '.status'

echo -e "\n=== Check Complete ==="
```

### Weekly Tasks

| Day | Task |
|---|---|
| Monday | Review performance metrics, identify bottlenecks |
| Wednesday | Test backup recovery to staging |
| Friday | DR drill (if scheduled), review alerts |
| Weekly | Check disk space, review logs |

---

## Common Issues & Solutions

### Issue: High API Latency (>2 seconds)

```bash
# 1. Check what's slow
curl -X POST http://localhost:8000/api/v1/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "language": "en"}' \
    -w "\nLatency: %{time_total}s\n"

# 2. Trace bottleneck
# a) RAG retrieval slow?
docker-compose logs rag-service | grep "retrieval_duration"

# b) LLM inference slow?
docker-compose logs llm-service | grep "inference_duration"

# c) Network slow?
ping postgres redis milvus

# 3. Fix
# - If RAG slow: increase RAG_TOP_K in .env
# - If LLM slow: reduce LLM_GPU_MEMORY_UTILIZATION
# - If network: check Docker network connectivity
```

### Issue: GPU Memory Errors (Out of Memory)

```bash
# 1. Check GPU
nvidia-smi

# 2. Reduce memory utilization
# Edit .env:
LLM_GPU_MEMORY_UTILIZATION=0.70  # from 0.85

# 3. Restart service
docker-compose restart llm-service

# 4. Monitor
watch -n 1 nvidia-smi
```

### Issue: Disk Space Full

```bash
# 1. Find large files
du -sh /mnt/data/* | sort -rh

# 2. Cleanup old data
# Delete documents >6 months old
docker-compose exec -T postgres psql -U ragqa_user -d ragqa \
    -c "DELETE FROM documents WHERE created_at < now() - interval '180 days'"

# 3. Clear caches
docker-compose exec -T redis redis-cli FLUSHALL

# 4. Check space
df -h /mnt/data
```

---

## Performance Baselines

Expected performance metrics:

```
API Latency (95th percentile):   <2000ms
Chat Response Time:              <5000ms (with streaming)
Search Response Time:            <3000ms
Cache Hit Rate:                  >70%
GPU Utilization:                 60-85%
Error Rate:                      <0.5%
Uptime:                          >99.5%
```

---

**Last Updated:** February 24, 2026
