#!/bin/bash
# ============================================================================
# Deep Health Check Script
# Verifies all service dependencies and critical functionality
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "=========================================="
echo "RAG-QA System Health Check"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

HEALTH_OK=0
HEALTH_WARN=0
HEALTH_FAIL=0

# Function to check service health
check_service() {
    local service=$1
    local host=$2
    local port=$3
    local type=$4  # http or tcp

    echo -n "Checking $service... "

    if [ "$type" = "http" ]; then
        local endpoint=$5
        local response=$(curl -s -o /dev/null -w "%{http_code}" "http://$host:$port$endpoint" 2>/dev/null || echo "000")
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            HEALTH_OK=$((HEALTH_OK + 1))
        else
            echo -e "${RED}✗ Failed (HTTP $response)${NC}"
            HEALTH_FAIL=$((HEALTH_FAIL + 1))
        fi
    else  # tcp
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e "${GREEN}✓ Healthy${NC}"
            HEALTH_OK=$((HEALTH_OK + 1))
        else
            echo -e "${RED}✗ Failed (Connection refused)${NC}"
            HEALTH_FAIL=$((HEALTH_FAIL + 1))
        fi
    fi
}

# ============================================================================
# DATABASE CHECKS
# ============================================================================
echo "DATABASE SERVICES:"
check_service "PostgreSQL (main)" "postgres" "5432" "tcp"
check_service "PostgreSQL (Langfuse)" "langfuse-postgres" "5433" "tcp"
check_service "Redis" "redis" "6379" "tcp"

echo ""
echo "VECTOR & METADATA STORES:"
check_service "Milvus" "milvus" "19530" "tcp"
check_service "etcd" "etcd" "2379" "tcp"

# ============================================================================
# CORE SERVICES
# ============================================================================
echo ""
echo "CORE SERVICES:"
check_service "API Gateway" "api-gateway" "8000" "http" "/health"
check_service "RAG Service" "rag-service" "8001" "http" "/health"
check_service "LLM Service" "llm-service" "8002" "http" "/v1/models"
check_service "Speech Service" "speech-service" "8003" "http" "/health"
check_service "Translation Service" "translation-service" "8004" "http" "/health"
check_service "OCR Service" "ocr-service" "8005" "http" "/health"
check_service "Data Ingestion" "data-ingestion" "8006" "http" "/health"
check_service "Model Training" "model-training" "8007" "http" "/health"

# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================
echo ""
echo "MONITORING & OBSERVABILITY:"
check_service "Prometheus" "prometheus" "9090" "http" "/-/healthy"
check_service "Grafana" "grafana" "3000" "http" "/api/health"
check_service "Langfuse" "langfuse" "3001" "http" "/health"
check_service "Loki" "loki" "3100" "http" "/ready"
check_service "DCGM Exporter" "dcgm-exporter" "9400" "http" "/metrics"

# ============================================================================
# NGINX PROXY
# ============================================================================
echo ""
echo "REVERSE PROXY:"
check_service "NGINX (HTTP)" "nginx" "80" "http" "/health"

# ============================================================================
# DEEP CHECKS
# ============================================================================
echo ""
echo "DEEP DEPENDENCY CHECKS:"

# Check PostgreSQL connectivity
echo -n "PostgreSQL database connectivity... "
if PGPASSWORD="${POSTGRES_PASSWORD}" psql -h postgres -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    HEALTH_OK=$((HEALTH_OK + 1))
else
    echo -e "${RED}✗ Failed${NC}"
    HEALTH_FAIL=$((HEALTH_FAIL + 1))
fi

# Check Redis connectivity
echo -n "Redis connectivity... "
if redis-cli -h redis -p 6379 -a "${REDIS_PASSWORD}" ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✓${NC}"
    HEALTH_OK=$((HEALTH_OK + 1))
else
    echo -e "${RED}✗ Failed${NC}"
    HEALTH_FAIL=$((HEALTH_FAIL + 1))
fi

# Check Milvus connectivity
echo -n "Milvus connectivity... "
if timeout 5 python3 -c "
from pymilvus import connections
connections.connect('default', host='milvus', port=19530)
connections.disconnect('default')
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    HEALTH_OK=$((HEALTH_OK + 1))
else
    echo -e "${YELLOW}⚠ Check manually${NC} (pymilvus may not be installed)"
    HEALTH_WARN=$((HEALTH_WARN + 1))
fi

# Check S3 connectivity
echo -n "S3 connectivity... "
if timeout 5 python3 -c "
import boto3
client = boto3.client('s3', region_name='${AWS_DEFAULT_REGION:-ap-south-1}', aws_access_key_id='${AWS_ACCESS_KEY_ID}', aws_secret_access_key='${AWS_SECRET_ACCESS_KEY}')
client.list_buckets()
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    HEALTH_OK=$((HEALTH_OK + 1))
else
    echo -e "${YELLOW}⚠ Check manually${NC} (S3 may not be accessible)"
    HEALTH_WARN=$((HEALTH_WARN + 1))
fi

# Check Prometheus scrape targets
echo -n "Prometheus targets... "
TARGETS=$(curl -s http://prometheus:9090/api/v1/targets 2>/dev/null | grep -c '"job_name"' || echo "0")
if [ "$TARGETS" -gt "10" ]; then
    echo -e "${GREEN}✓ ($TARGETS targets)${NC}"
    HEALTH_OK=$((HEALTH_OK + 1))
else
    echo -e "${YELLOW}⚠ Only $TARGETS targets${NC}"
    HEALTH_WARN=$((HEALTH_WARN + 1))
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "=========================================="
echo "HEALTH CHECK SUMMARY"
echo "=========================================="
echo -e "Healthy:  ${GREEN}$HEALTH_OK${NC}"
echo -e "Warnings: ${YELLOW}$HEALTH_WARN${NC}"
echo -e "Failed:   ${RED}$HEALTH_FAIL${NC}"

if [ $HEALTH_FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All systems operational${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some services are unhealthy${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs [service-name]"
    echo "  2. Verify .env variables"
    echo "  3. Ensure Docker network is working: docker network inspect rag-network"
    echo "  4. Check disk space: df -h"
    echo "  5. Check available memory: free -h"
    exit 1
fi
