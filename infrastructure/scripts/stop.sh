#!/bin/bash
# ============================================================================
# Stop Services Script
# Graceful shutdown of all services
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "=========================================="
echo "Stopping RAG-QA Services"
echo "=========================================="

cd "$PROJECT_ROOT"

echo "Stopping Docker Compose services..."
docker-compose -f docker-compose.yml down --remove-orphans

echo ""
echo "Waiting for containers to stop gracefully..."
sleep 3

# Check for any remaining containers
REMAINING=$(docker ps -a --filter "label=com.ragqa.service" --format "{{.Names}}" 2>/dev/null || true)

if [ -n "$REMAINING" ]; then
    echo "WARNING: Some containers are still running:"
    echo "$REMAINING"
    echo ""
    echo "Force stopping..."
    docker ps -a --filter "label=com.ragqa.service" --format "{{.ID}}" | xargs -r docker kill
fi

echo ""
echo "=========================================="
echo "✓ All services stopped"
echo "=========================================="
echo ""
echo "To start again: ./infrastructure/scripts/start.sh"
echo ""
