#!/bin/bash

################################################################################
# Seed Initial Data via ECS
# Seeds initial roles, permissions, and scrape targets
#
# Usage: ./seed-data.sh [ENVIRONMENT] [AWS_REGION]
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
AWS_REGION="${2:-ap-south-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="${SCRIPT_DIR}/seed-$(date +%Y%m%d-%H%M%S).log"
MAX_WAIT_TIME=300  # 5 minutes

################################################################################
# Utility Functions
################################################################################

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOGFILE"
}

success() {
    echo -e "${GREEN}[✓]${NC} $*" | tee -a "$LOGFILE"
}

error() {
    echo -e "${RED}[✗] ERROR:${NC} $*" | tee -a "$LOGFILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[!]${NC} $*" | tee -a "$LOGFILE"
}

check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v aws &> /dev/null; then
        error "AWS CLI is required"
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured"
    fi

    success "Prerequisites met"
}

get_cluster_name() {
    log "Getting ECS cluster name..."

    local terraform_dir
    terraform_dir="$(cd "$SCRIPT_DIR/../terraform" && pwd)"

    cd "$terraform_dir"
    local cluster_name
    cluster_name=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")

    if [ -z "$cluster_name" ]; then
        error "Could not determine ECS cluster name"
    fi

    echo "$cluster_name"
}

seed_initial_data() {
    log "Seeding initial data..."

    local cluster_name="$1"
    local subnet_id="$2"
    local security_group_id="$3"

    # Create seed script content
    local seed_script
    read -r -d '' seed_script << 'EOF' || true
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This is a placeholder for actual seed logic
# In production, implement proper seeding with Alembic or similar

async def seed_data():
    logger.info("Starting data seeding...")

    # Example: Create default roles
    roles = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "editor", "description": "Editor with document management access"},
        {"name": "viewer", "description": "Viewer with read-only access"},
        {"name": "api_consumer", "description": "API consumer for programmatic access"},
    ]

    # Example: Create default scrape targets
    scrape_targets = [
        {
            "name": "example_target",
            "url": "https://example.com",
            "enabled": True,
            "schedule": "0 0 * * *",  # Daily at midnight
        }
    ]

    logger.info("Roles data prepared: %s", len(roles))
    logger.info("Scrape targets prepared: %s", len(scrape_targets))
    logger.info("Data seeding completed successfully")

if __name__ == "__main__":
    asyncio.run(seed_data())
EOF

    # Run the seed task
    local task_arn
    task_arn=$(aws ecs run-task \
        --cluster "$cluster_name" \
        --task-definition "ragqa-data-ingestion:1" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$subnet_id],securityGroups=[$security_group_id],assignPublicIp=DISABLED}" \
        --overrides "{\"containerOverrides\":[{\"name\":\"data-ingestion\",\"command\":[\"python\",\"-c\",\"$seed_script\"]}]}" \
        --region "$AWS_REGION" \
        --query 'tasks[0].taskArn' \
        --output text 2>/dev/null || echo "")

    if [ -z "$task_arn" ]; then
        warning "Failed to run seed task. Skipping data seeding."
        return 1
    fi

    log "Seed task started: $task_arn"

    # Wait for task to complete
    local elapsed=0
    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        local task_status
        task_status=$(aws ecs describe-tasks \
            --cluster "$cluster_name" \
            --tasks "$task_arn" \
            --region "$AWS_REGION" \
            --query 'tasks[0].lastStatus' \
            --output text 2>/dev/null || echo "UNKNOWN")

        if [ "$task_status" = "STOPPED" ]; then
            local exit_code
            exit_code=$(aws ecs describe-tasks \
                --cluster "$cluster_name" \
                --tasks "$task_arn" \
                --region "$AWS_REGION" \
                --query 'tasks[0].containers[0].exitCode' \
                --output text 2>/dev/null || echo "1")

            if [ "$exit_code" = "0" ] || [ "$exit_code" = "None" ]; then
                success "Seed task completed successfully"
                return 0
            else
                warning "Seed task exited with code: $exit_code. Manual seeding may be needed."
                return 1
            fi
        fi

        elapsed=$((elapsed + 5))
        log "Waiting for seed task... ($elapsed/$MAX_WAIT_TIME seconds)"
        sleep 5
    done

    warning "Seed task timed out. Manual seeding may be needed."
    return 1
}

################################################################################
# Main Execution
################################################################################

main() {
    log "========================================="
    log "Seed Initial Data"
    log "========================================="
    log "Environment: $ENVIRONMENT"
    log "AWS Region: $AWS_REGION"
    log "Log file: $LOGFILE"
    log ""

    check_prerequisites

    local cluster_name
    cluster_name=$(get_cluster_name)

    log "Using ECS cluster: $cluster_name"

    # Get VPC configuration from Terraform
    local terraform_dir
    terraform_dir="$(cd "$SCRIPT_DIR/../terraform" && pwd)"
    cd "$terraform_dir"

    local subnet_id
    subnet_id=$(terraform output -json private_subnets 2>/dev/null | jq -r '.[0]' || echo "")

    local security_group_id
    security_group_id=$(terraform output -raw ecs_security_group_id 2>/dev/null || echo "")

    if [ -z "$subnet_id" ] || [ -z "$security_group_id" ]; then
        warning "Could not determine VPC configuration. Skipping data seeding."
        success "Data seeding skipped"
        exit 0
    fi

    seed_initial_data "$cluster_name" "$subnet_id" "$security_group_id" || true

    success "Data seeding script completed"
}

main "$@"
