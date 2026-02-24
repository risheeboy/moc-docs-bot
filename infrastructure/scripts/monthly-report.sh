#!/bin/bash
# ============================================================================
# Monthly Performance Report Generator
# Generates markdown report from Prometheus metrics for the past month
# ============================================================================

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
REPORTS_DIR="${PROJECT_ROOT}/reports"
TIMESTAMP=$(date +%Y-%m-%d)
REPORT_FILE="$REPORTS_DIR/monthly_report_${TIMESTAMP}.md"

mkdir -p "$REPORTS_DIR"

echo "=========================================="
echo "Generating Monthly Performance Report"
echo "Report Date: $TIMESTAMP"
echo "=========================================="
echo ""

# Load environment
set -a
source "$PROJECT_ROOT/.env"
set +a

# Function to query Prometheus
query_prometheus() {
    local query=$1
    curl -s "http://prometheus:9090/api/v1/query?query=${query}" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "N/A"
}

# Function to query Prometheus range
query_prometheus_range() {
    local query=$1
    local start=$2
    local end=$3
    curl -s "http://prometheus:9090/api/v1/query_range?query=${query}&start=${start}&end=${end}&step=1d" | jq -r '.data.result' 2>/dev/null
}

# Generate report
cat > "$REPORT_FILE" << EOF
# RAG-QA System Monthly Performance Report

**Report Date:** $TIMESTAMP
**Period:** $(date -d "30 days ago" +%Y-%m-%d) to $TIMESTAMP

---

## Executive Summary

Monthly performance report for the RAG-Based Hindi QA System deployed at the Ministry of Culture.

---

## System Availability

| Service | Uptime | Status |
|---------|--------|--------|
| API Gateway | $(query_prometheus 'up{job="api-gateway"}') | $([ "$(query_prometheus 'up{job="api-gateway"}')" = "1" ] && echo "✓" || echo "✗") |
| RAG Service | $(query_prometheus 'up{job="rag-service"}') | $([ "$(query_prometheus 'up{job="rag-service"}')" = "1" ] && echo "✓" || echo "✗") |
| LLM Service | $(query_prometheus 'up{job="llm-service"}') | $([ "$(query_prometheus 'up{job="llm-service"}')" = "1" ] && echo "✓" || echo "✗") |
| Speech Service | $(query_prometheus 'up{job="speech-service"}') | $([ "$(query_prometheus 'up{job="speech-service"}')" = "1" ] && echo "✓" || echo "✗") |
| PostgreSQL | $(query_prometheus 'up{job="postgres"}') | $([ "$(query_prometheus 'up{job="postgres"}')" = "1" ] && echo "✓" || echo "✗") |

---

## Performance Metrics

### API Gateway

**Request Rate:**
\`\`\`
Current: $(query_prometheus 'rate(http_requests_total{job="api-gateway"}[1m])') requests/second
\`\`\`

**Latency (p95):**
\`\`\`
$(query_prometheus 'histogram_quantile(0.95, http_request_duration_seconds_bucket{job="api-gateway"})') seconds
\`\`\`

**Error Rate:**
\`\`\`
$(query_prometheus 'rate(http_requests_total{job="api-gateway", status_code=~"5.."}[1m])') errors/second
\`\`\`

---

### RAG Service

**Retrieval Latency (p95):**
\`\`\`
$(query_prometheus 'histogram_quantile(0.95, rag_retrieval_duration_seconds_bucket)') seconds
\`\`\`

**Cache Hit Rate:**
\`\`\`
$(query_prometheus 'rate(rag_cache_hit_total[1m]) / (rate(rag_cache_hit_total[1m]) + rate(rag_cache_miss_total[1m]))') (percentage)
\`\`\`

---

### LLM Service

**Token Generation Rate:**
\`\`\`
$(query_prometheus 'rate(llm_tokens_generated_total[1m])') tokens/second
\`\`\`

**Inference Latency (p99):**
\`\`\`
$(query_prometheus 'histogram_quantile(0.99, llm_inference_duration_seconds_bucket)') seconds
\`\`\`

---

## GPU Metrics

**GPU Memory Usage:**
\`\`\`
$(query_prometheus 'avg(DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_FREE * 100)') %
\`\`\`

**GPU Utilization:**
\`\`\`
$(query_prometheus 'avg(DCGM_FI_DEV_GPU_UTIL)') %
\`\`\`

**GPU Temperature (Max):**
\`\`\`
$(query_prometheus 'max(DCGM_FI_DEV_GPU_TEMP)') °C
\`\`\`

---

## Storage Metrics

**PostgreSQL Size:**
\`\`\`
$(docker exec rag-qa-postgres psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tc "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));" 2>/dev/null || echo "N/A")
\`\`\`

**MinIO Bucket Usage:**
\`\`\`
N/A (requires mc tool)
\`\`\`

---

## Database Performance

**PostgreSQL Connections:**
\`\`\`
$(docker exec rag-qa-postgres psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tc "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null || echo "N/A")
\`\`\`

**Active Queries:**
\`\`\`
$(docker exec rag-qa-postgres psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -tc "SELECT count(*) FROM pg_stat_statements WHERE mean_time > 1000;" 2>/dev/null || echo "N/A")
\`\`\`

---

## Cache Performance

**Redis Connected Clients:**
\`\`\`
$(redis-cli -h redis -p 6379 -a ${REDIS_PASSWORD} INFO clients 2>/dev/null | grep connected_clients || echo "N/A")
\`\`\`

**Redis Memory Usage:**
\`\`\`
$(redis-cli -h redis -p 6379 -a ${REDIS_PASSWORD} INFO memory 2>/dev/null | grep used_memory_human || echo "N/A")
\`\`\`

---

## Alerts & Incidents

### High Latency Events
- Total incidents: $(curl -s "http://prometheus:9090/api/v1/query?query=count(ALERTS{alertname='HighLatency'})" 2>/dev/null | jq -r '.data.result[0].value[1]' || echo "0")

### Service Downtime Events
- Total incidents: $(curl -s "http://prometheus:9090/api/v1/query?query=count(ALERTS{alertname='ServiceDown'})" 2>/dev/null | jq -r '.data.result[0].value[1]' || echo "0")

### GPU Memory Issues
- Total incidents: $(curl -s "http://prometheus:9090/api/v1/query?query=count(ALERTS{alertname='HighGPUMemory'})" 2>/dev/null | jq -r '.data.result[0].value[1]' || echo "0")

---

## Recommendations

1. **Performance Optimization**
   - Monitor API latency trends
   - Optimize slow database queries
   - Fine-tune GPU memory allocation

2. **Capacity Planning**
   - Evaluate storage growth rate
   - Plan for multi-GPU scaling if needed
   - Consider load balancing setup

3. **Reliability**
   - Ensure automated backups are running
   - Test disaster recovery procedures
   - Monitor error rates for patterns

---

## System Configuration

- **API Gateway:** http://api-gateway:8000
- **RAG Service:** http://rag-service:8001
- **LLM Service:** http://llm-service:8002
- **Monitoring:** http://prometheus:9090, http://grafana:3000

---

**Report Generated:** $(date)
**Generated By:** Automated Monthly Report Script

EOF

echo ""
echo "✓ Report generated: $REPORT_FILE"
echo ""
cat "$REPORT_FILE"
