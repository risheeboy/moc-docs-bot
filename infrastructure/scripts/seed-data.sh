#!/bin/bash
# ============================================================================
# Seed Data Script
# Triggers initial web scraping and data ingestion from Ministry of Culture sites
# ============================================================================

set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

echo "=========================================="
echo "Seeding Initial Data"
echo "=========================================="
echo ""

# Load environment
set -a
source "$PROJECT_ROOT/.env"
set +a

# Wait for services to be ready
echo "Waiting for services to be ready..."
RETRIES=0
MAX_RETRIES=30

while ! curl -s http://data-ingestion:8006/health > /dev/null 2>&1; do
    if [ $RETRIES -eq $MAX_RETRIES ]; then
        echo "ERROR: Data ingestion service failed to start"
        exit 1
    fi
    RETRIES=$((RETRIES + 1))
    sleep 2
done

echo "✓ Services ready"
echo ""

# ============================================================================
# TARGET MINISTRY SITES
# ============================================================================

SITES=(
    "https://culture.gov.in"
    "https://indiacode.nic.in"
    "https://asi.nic.in"
    "https://ignca.gov.in"
    "https://iccr.gov.in"
    "https://nmaind.gov.in"
    "https://archiveindia.gov.in"
)

echo "Triggering web scraping for Ministry sites..."
echo ""

for site in "${SITES[@]}"; do
    echo "Queuing: $site"

    # Trigger ingestion job
    RESPONSE=$(curl -s -X POST "http://data-ingestion:8006/jobs/trigger" \
        -H "Content-Type: application/json" \
        -d "{
            \"target_urls\": [\"$site\"],
            \"spider_type\": \"auto\",
            \"force_rescrape\": false
        }" 2>/dev/null || echo "{}")

    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // "unknown"' 2>/dev/null || echo "unknown")

    if [ "$JOB_ID" != "unknown" ] && [ "$JOB_ID" != "null" ]; then
        echo "  ✓ Job started: $JOB_ID"
    else
        echo "  ⚠ Failed to queue (service may not be ready yet)"
    fi

    sleep 2
done

echo ""
echo "=========================================="
echo "✓ Ingestion jobs queued"
echo "=========================================="
echo ""
echo "Monitoring ingestion progress..."
echo "Check status: curl http://localhost:8006/jobs/status?job_id=<job_id>"
echo ""
echo "Logs can be viewed with:"
echo "  docker-compose logs -f data-ingestion"
echo ""
echo "Note: Initial scraping may take 30-60 minutes depending on site size"
echo ""
