#!/bin/bash
# ============================================================================
# Start Services Script
# Brings up all services with health checks
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "=========================================="
echo "Starting RAG-QA Services"
echo "=========================================="

cd "$PROJECT_ROOT"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    echo "Run: ./infrastructure/scripts/init.sh first"
    exit 1
fi

# Load environment
set -a
source .env
set +a

echo "Starting Docker Compose services..."
docker-compose -f docker-compose.yml up -d --pull=never

echo ""
echo "Waiting for services to become healthy..."
echo ""

# Array of services to check
SERVICES=(
    "postgres:5432"
    "redis:6379"
    "etcd:2379"
    "milvus:19530"
    "minio:9000"
    "api-gateway:8000"
    "rag-service:8001"
    "llm-service:8002"
    "prometheus:9090"
    "grafana:3000"
    "langfuse:3001"
    "loki:3100"
)

# Wait for services to be available
MAX_RETRIES=60
RETRY_DELAY=2

for service in "${SERVICES[@]}"; do
    SERVICE_HOST="${service%:*}"
    SERVICE_PORT="${service#*:}"
    RETRIES=0

    echo -n "Waiting for $SERVICE_HOST:$SERVICE_PORT..."
    while ! nc -z "$SERVICE_HOST" "$SERVICE_PORT" 2>/dev/null; do
        if [ $RETRIES -eq $MAX_RETRIES ]; then
            echo " TIMEOUT"
            exit 1
        fi
        echo -n "."
        RETRIES=$((RETRIES + 1))
        sleep $RETRY_DELAY
    done
    echo " ✓"
done

echo ""
echo "=========================================="
echo "✓ All services started successfully!"
echo "=========================================="
echo ""
echo "Service URLs:"
echo "  - API Gateway:    http://localhost:8000"
echo "  - Chat Widget:    http://localhost:80"
echo "  - Search Page:    http://localhost:80/search"
echo "  - Admin Panel:    http://localhost:80/admin"
echo "  - Grafana:        http://localhost:3000 (admin/admin)"
echo "  - Langfuse:       http://localhost:3001"
echo "  - Prometheus:     http://localhost:9090"
echo "  - MinIO Console:  http://localhost:9001"
echo ""
echo "Check health: ./infrastructure/scripts/health-check.sh"
echo "View logs:    docker-compose logs -f [service-name]"
echo ""
