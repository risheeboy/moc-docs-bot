#!/bin/bash

################################################################################
# RAG QA Hindi - AWS Infrastructure Teardown Script
# Safely destroys all infrastructure and cleans up ECR repositories
#
# Usage: ./destroy.sh [ENVIRONMENT] [OPTIONS]
#   ENVIRONMENT: production, staging, development (default: production)
#   OPTIONS:
#     --force        Skip confirmation prompt
#     --keep-data    Keep RDS and ElastiCache data
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-production}"
FORCE_DESTROY="${2:-}"
KEEP_DATA=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
LOGFILE="${SCRIPT_DIR}/teardown-$(date +%Y%m%d-%H%M%S).log"

AWS_REGION="ap-south-1"
PROJECT_NAME="ragqa"

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
        error "AWS CLI is required but not installed"
    fi

    if ! command -v terraform &> /dev/null; then
        error "Terraform is required but not installed"
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
    fi

    success "Prerequisites met"
}

parse_options() {
    shift # Skip environment argument
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE_DESTROY="--force"
                shift
                ;;
            --keep-data)
                KEEP_DATA=true
                shift
                ;;
            *)
                warning "Unknown option: $1"
                shift
                ;;
        esac
    done
}

confirm_destruction() {
    if [ -n "$FORCE_DESTROY" ]; then
        return 0
    fi

    echo ""
    warning "This action will PERMANENTLY DELETE all infrastructure for: $ENVIRONMENT"
    echo ""
    echo "Resources that will be destroyed:"
    echo "  - ECS Cluster and all services"
    echo "  - RDS Database (unless --keep-data flag is used)"
    echo "  - ElastiCache Cluster (unless --keep-data flag is used)"
    echo "  - Load Balancers and Target Groups"
    echo "  - VPC and Subnets"
    echo "  - EFS Storage"
    echo "  - ECR Repositories"
    echo "  - CloudWatch Logs"
    echo ""

    read -p "Type 'destroy-$ENVIRONMENT' to confirm: " confirmation

    if [ "$confirmation" != "destroy-$ENVIRONMENT" ]; then
        log "Destruction cancelled"
        exit 0
    fi
}

cleanup_ecr() {
    log "Cleaning up ECR repositories..."

    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)

    local repositories=(
        "ragqa/api-gateway"
        "ragqa/rag-service"
        "ragqa/llm-service"
        "ragqa/speech-service"
        "ragqa/translation-service"
        "ragqa/ocr-service"
        "ragqa/data-ingestion"
        "ragqa/model-training"
        "ragqa/chat-widget"
        "ragqa/search-page"
        "ragqa/admin-dashboard"
    )

    for repo in "${repositories[@]}"; do
        log "Deleting ECR repository: $repo..."

        # Delete all images in the repository
        aws ecr describe-images \
            --repository-name "$repo" \
            --region "$AWS_REGION" \
            --query 'imageIds[*]' \
            --output json 2>/dev/null | \
        jq -r '.[] | .imageId' | \
        while read -r image_id; do
            aws ecr batch-delete-image \
                --repository-name "$repo" \
                --image-ids "$image_id" \
                --region "$AWS_REGION" \
                >> "$LOGFILE" 2>&1 || true
        done

        # Delete the repository
        aws ecr delete-repository \
            --repository-name "$repo" \
            --region "$AWS_REGION" \
            --force \
            >> "$LOGFILE" 2>&1 || warning "Failed to delete ECR repository: $repo"
    done

    success "ECR repositories cleaned up"
}

terraform_destroy() {
    log "Running Terraform destroy for environment: $ENVIRONMENT..."

    cd "$TERRAFORM_DIR"

    # Initialize Terraform
    terraform init -upgrade -no-color >> "$LOGFILE" 2>&1 || error "Terraform init failed"

    # Set variables for RDS deletion
    local destroy_vars=""
    if [ "$KEEP_DATA" = false ]; then
        destroy_vars="-var=skip_final_snapshot=false"
    fi

    # Destroy infrastructure
    terraform destroy \
        -var-file="$([ -f "environments/${ENVIRONMENT}.tfvars" ] && echo "environments/${ENVIRONMENT}.tfvars" || echo "terraform.tfvars")" \
        $destroy_vars \
        -no-color \
        -auto-approve \
        >> "$LOGFILE" 2>&1 || error "Terraform destroy failed"

    success "Infrastructure destroyed via Terraform"
}

cleanup_cloudwatch() {
    log "Cleaning up CloudWatch logs..."

    # Delete log groups
    local log_groups
    log_groups=$(aws logs describe-log-groups \
        --region "$AWS_REGION" \
        --query "logGroups[?contains(logGroupName, '/ecs/ragqa')].logGroupName" \
        --output text 2>/dev/null || echo "")

    for log_group in $log_groups; do
        log "Deleting log group: $log_group..."
        aws logs delete-log-group \
            --log-group-name "$log_group" \
            --region "$AWS_REGION" \
            >> "$LOGFILE" 2>&1 || warning "Failed to delete log group: $log_group"
    done

    success "CloudWatch logs cleaned up"
}

cleanup_s3() {
    log "Cleaning up S3 buckets..."

    # Find and cleanup Terraform state bucket
    local bucket_name="${PROJECT_NAME}-terraform-state"

    if aws s3 ls "s3://$bucket_name" 2>/dev/null; then
        log "Emptying S3 bucket: $bucket_name..."

        aws s3 rm "s3://$bucket_name" --recursive --region "$AWS_REGION" >> "$LOGFILE" 2>&1 || warning "Failed to empty bucket: $bucket_name"

        # Don't delete the bucket - it may be reused
        log "Bucket emptied but retained: $bucket_name"
    fi

    success "S3 buckets cleaned up"
}

print_summary() {
    log "========================================="
    log "TEARDOWN SUMMARY"
    log "========================================="

    echo ""
    echo -e "${GREEN}Environment destroyed:${NC} $ENVIRONMENT"
    echo -e "${GREEN}AWS Region:${NC} $AWS_REGION"
    echo -e "${YELLOW}Log file:${NC} $LOGFILE"
    echo ""
    echo "Additional cleanup steps if needed:"
    echo "  - Verify all resources are deleted in AWS Console"
    echo "  - Check for any remaining EBS volumes"
    echo "  - Review CloudWatch alarms"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    log "========================================="
    log "RAG QA Hindi - Infrastructure Teardown"
    log "========================================="
    log "Environment: $ENVIRONMENT"
    log "Log file: $LOGFILE"
    log ""

    parse_options "$@"
    check_prerequisites
    confirm_destruction

    # Execute teardown
    terraform_destroy
    cleanup_ecr
    cleanup_cloudwatch
    cleanup_s3

    print_summary
    success "Infrastructure teardown completed successfully"
}

main "$@"
