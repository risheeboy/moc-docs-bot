#!/bin/bash

################################################################################
# Run Database Migrations via ECS
# Executes database migrations using ECS RunTask
#
# Usage: ./run-migrations.sh [ENVIRONMENT] [AWS_REGION]
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
LOGFILE="${SCRIPT_DIR}/migrations-$(date +%Y%m%d-%H%M%S).log"
MAX_WAIT_TIME=600  # 10 minutes

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
        error "Could not determine ECS cluster name. Ensure Terraform has been applied."
    fi

    echo "$cluster_name"
}

run_migrations_task() {
    log "Running migrations via ECS..."

    local cluster_name="$1"
    local subnet_id="$2"
    local security_group_id="$3"

    # Run the migration task
    local task_arn
    task_arn=$(aws ecs run-task \
        --cluster "$cluster_name" \
        --task-definition "ragqa-api-gateway:1" \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$subnet_id],securityGroups=[$security_group_id],assignPublicIp=DISABLED}" \
        --overrides "{\"containerOverrides\":[{\"name\":\"api-gateway\",\"command\":[\"python\",\"-m\",\"alembic\",\"upgrade\",\"head\"]}]}" \
        --region "$AWS_REGION" \
        --query 'tasks[0].taskArn' \
        --output text 2>/dev/null || echo "")

    if [ -z "$task_arn" ]; then
        warning "Failed to run migration task. Skipping database migrations."
        return 1
    fi

    log "Migration task started: $task_arn"

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
            # Check exit code
            local exit_code
            exit_code=$(aws ecs describe-tasks \
                --cluster "$cluster_name" \
                --tasks "$task_arn" \
                --region "$AWS_REGION" \
                --query 'tasks[0].containers[0].exitCode' \
                --output text 2>/dev/null || echo "1")

            if [ "$exit_code" = "0" ] || [ "$exit_code" = "None" ]; then
                success "Migration task completed successfully"
                return 0
            else
                error "Migration task failed with exit code: $exit_code"
            fi
        fi

        elapsed=$((elapsed + 5))
        log "Waiting for migration task... ($elapsed/$MAX_WAIT_TIME seconds)"
        sleep 5
    done

    error "Migration task timed out after $MAX_WAIT_TIME seconds"
}

################################################################################
# Main Execution
################################################################################

main() {
    log "========================================="
    log "Run Database Migrations"
    log "========================================="
    log "Environment: $ENVIRONMENT"
    log "AWS Region: $AWS_REGION"
    log "Log file: $LOGFILE"
    log ""

    check_prerequisites

    local cluster_name
    cluster_name=$(get_cluster_name)

    log "Using ECS cluster: $cluster_name"

    # Get VPC and security group details from Terraform
    local terraform_dir
    terraform_dir="$(cd "$SCRIPT_DIR/../terraform" && pwd)"
    cd "$terraform_dir"

    local subnet_id
    subnet_id=$(terraform output -json private_subnets 2>/dev/null | jq -r '.[0]' || echo "")

    local security_group_id
    security_group_id=$(terraform output -raw ecs_security_group_id 2>/dev/null || echo "")

    if [ -z "$subnet_id" ] || [ -z "$security_group_id" ]; then
        warning "Could not determine VPC configuration. Skipping migrations."
        success "Database migrations skipped"
        exit 0
    fi

    run_migrations_task "$cluster_name" "$subnet_id" "$security_group_id" || true

    success "Migration script completed"
}

main "$@"
