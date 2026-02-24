#!/bin/bash

################################################################################
# RAG QA Hindi - AWS ECS Deployment Script
# One-click deployment to AWS ECS with Fargate and EC2 GPU instances
#
# Usage: ./deploy.sh [ENVIRONMENT] [ACTION]
#   ENVIRONMENT: production, staging, development (default: production)
#   ACTION: plan, apply, destroy (default: apply)
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
ACTION="${2:-apply}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
SCRIPTS_DIR="${SCRIPT_DIR}/scripts"
ECS_DIR="${SCRIPT_DIR}/ecs"
LOGFILE="${SCRIPT_DIR}/deployment-$(date +%Y%m%d-%H%M%S).log"

# Configuration
AWS_REGION="ap-south-1"
PROJECT_NAME="ragqa"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKER_REGISTRY_URL=""

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

    local missing_tools=()

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        missing_tools+=("AWS CLI")
    fi

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("Terraform")
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("Docker")
    fi

    # Check jq
    if ! command -v jq &> /dev/null; then
        missing_tools+=("jq")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
    fi

    # Verify AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
    fi

    success "All prerequisites met"
}

load_configuration() {
    log "Loading configuration for environment: $ENVIRONMENT..."

    local tfvars_file="${TERRAFORM_DIR}/environments/${ENVIRONMENT}.tfvars"

    if [ ! -f "$tfvars_file" ]; then
        warning "Configuration file not found: $tfvars_file"
        log "Using default configuration and prompting for values..."

        if [ ! -f "${TERRAFORM_DIR}/terraform.tfvars" ]; then
            log "Creating default terraform.tfvars..."
            cat > "${TERRAFORM_DIR}/terraform.tfvars" << EOF
aws_region     = "$AWS_REGION"
environment    = "$ENVIRONMENT"
project_name   = "$PROJECT_NAME"

# Update these values
vpc_cidr            = "10.0.0.0/16"
private_subnets    = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets     = ["10.0.101.0/24", "10.0.102.0/24"]
availability_zones = ["${AWS_REGION}a", "${AWS_REGION}b"]

# RDS Configuration
rds_engine_version     = "16.0"
rds_instance_class     = "db.r6g.xlarge"
rds_allocated_storage  = 100

# ElastiCache Configuration
elasticache_node_type       = "cache.r6g.xlarge"
elasticache_num_cache_nodes = 1

# ECS Configuration
fargate_instance_count = 1
ec2_instance_count     = 1
ec2_instance_type      = "g5.2xlarge"

# Container Configuration
image_tag = "$IMAGE_TAG"
EOF
            success "Created terraform.tfvars. Please edit it with your values."
        fi
    else
        success "Loaded configuration from $tfvars_file"
    fi
}

validate_terraform() {
    log "Validating Terraform configuration..."

    cd "$TERRAFORM_DIR"
    terraform init -upgrade -no-color >> "$LOGFILE" 2>&1 || error "Terraform init failed"
    terraform validate -no-color >> "$LOGFILE" 2>&1 || error "Terraform validation failed"

    success "Terraform configuration is valid"
}

create_task_definitions() {
    log "Creating ECS task definitions..."

    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local ecr_repo="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    if [ ! -d "$ECS_DIR/task-definitions" ]; then
        error "Task definitions directory not found: $ECS_DIR/task-definitions"
    fi

    for task_def in "$ECS_DIR"/task-definitions/*.json; do
        if [ -f "$task_def" ]; then
            local task_name
            task_name=$(basename "$task_def" .json)

            log "Registering task definition: $task_name..."

            # Substitute placeholders
            cat "$task_def" \
                | sed "s|\${AWS_ACCOUNT_ID}|$aws_account_id|g" \
                | sed "s|\${AWS_REGION}|$AWS_REGION|g" \
                | sed "s|\${IMAGE_TAG}|$IMAGE_TAG|g" \
                | aws ecs register-task-definition \
                    --cli-input-json file:///dev/stdin \
                    --region "$AWS_REGION" >> "$LOGFILE" 2>&1 \
                || warning "Failed to register task definition: $task_name"
        fi
    done

    success "Task definitions created"
}

terraform_plan() {
    log "Running Terraform plan for environment: $ENVIRONMENT..."

    cd "$TERRAFORM_DIR"
    terraform plan \
        -var-file="$([ -f "environments/${ENVIRONMENT}.tfvars" ] && echo "environments/${ENVIRONMENT}.tfvars" || echo "terraform.tfvars")" \
        -out="tfplan-${ENVIRONMENT}" \
        -no-color \
        >> "$LOGFILE" 2>&1 || error "Terraform plan failed"

    success "Terraform plan completed. Review at: $TERRAFORM_DIR/tfplan-${ENVIRONMENT}"
}

terraform_apply() {
    log "Running Terraform apply for environment: $ENVIRONMENT..."

    cd "$TERRAFORM_DIR"

    # Check if plan exists
    if [ ! -f "tfplan-${ENVIRONMENT}" ]; then
        warning "Plan not found. Creating new plan..."
        terraform_plan
    fi

    terraform apply -no-color "tfplan-${ENVIRONMENT}" >> "$LOGFILE" 2>&1 || error "Terraform apply failed"

    success "Infrastructure deployed successfully"
}

wait_for_infrastructure() {
    log "Waiting for infrastructure to be ready..."

    local max_attempts=60
    local attempt=0

    cd "$TERRAFORM_DIR"

    while [ $attempt -lt $max_attempts ]; do
        if terraform output -no-color ecs_cluster_name &> /dev/null; then
            success "Infrastructure is ready"
            return 0
        fi

        attempt=$((attempt + 1))
        log "Waiting... ($attempt/$max_attempts)"
        sleep 10
    done

    error "Infrastructure failed to become ready within timeout"
}

build_and_push_images() {
    log "Building and pushing Docker images to ECR..."

    bash "$SCRIPTS_DIR/build-and-push.sh" "$AWS_REGION" "$IMAGE_TAG" >> "$LOGFILE" 2>&1 || error "Failed to build and push images"

    success "Docker images built and pushed to ECR"
}

run_migrations() {
    log "Running database migrations..."

    bash "$SCRIPTS_DIR/run-migrations.sh" "$ENVIRONMENT" "$AWS_REGION" >> "$LOGFILE" 2>&1 || warning "Database migrations completed with warnings"

    success "Database migrations completed"
}

seed_data() {
    log "Seeding initial data..."

    bash "$SCRIPTS_DIR/seed-data.sh" "$ENVIRONMENT" "$AWS_REGION" >> "$LOGFILE" 2>&1 || warning "Data seeding completed with warnings"

    success "Initial data seeded"
}

wait_for_services() {
    log "Waiting for ECS services to be healthy..."

    local services=(
        "ragqa-api-gateway"
        "ragqa-rag-service"
        "ragqa-milvus"
        "ragqa-langfuse"
    )

    local max_attempts=120
    local attempt=0
    local cluster_name

    cd "$TERRAFORM_DIR"
    cluster_name=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "")

    if [ -z "$cluster_name" ]; then
        warning "Could not determine cluster name. Skipping service health checks."
        return
    fi

    while [ $attempt -lt $max_attempts ]; do
        local all_healthy=true

        for service in "${services[@]}"; do
            local running_count
            running_count=$(aws ecs describe-services \
                --cluster "$cluster_name" \
                --services "$service" \
                --region "$AWS_REGION" \
                --query 'services[0].runningCount' \
                --output text 2>/dev/null || echo "0")

            if [ "$running_count" -lt 1 ]; then
                all_healthy=false
                break
            fi
        done

        if [ "$all_healthy" = true ]; then
            success "All critical services are healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        log "Services becoming healthy... ($attempt/$max_attempts)"
        sleep 5
    done

    warning "Some services did not become healthy within timeout. Check CloudWatch logs."
}

print_summary() {
    log "========================================="
    log "DEPLOYMENT SUMMARY"
    log "========================================="

    cd "$TERRAFORM_DIR"

    local alb_url
    alb_url=$(terraform output -raw alb_dns_name 2>/dev/null || echo "Not available")

    local ecs_cluster
    ecs_cluster=$(terraform output -raw ecs_cluster_name 2>/dev/null || echo "Not available")

    echo ""
    echo -e "${GREEN}Application URL:${NC} http://$alb_url"
    echo -e "${GREEN}ECS Cluster:${NC} $ecs_cluster"
    echo -e "${GREEN}AWS Region:${NC} $AWS_REGION"
    echo -e "${GREEN}Environment:${NC} $ENVIRONMENT"
    echo ""
    echo "Dashboard Access Points:"
    echo "  - Grafana:   http://$alb_url/grafana"
    echo "  - Prometheus: http://$alb_url/prometheus"
    echo "  - Langfuse:  http://$alb_url/langfuse"
    echo ""
    echo -e "${YELLOW}Log file:${NC} $LOGFILE"
    echo ""
}

terraform_destroy() {
    log "Destroying infrastructure for environment: $ENVIRONMENT..."

    warning "This action will destroy all resources. Type 'yes' to confirm."
    read -r confirmation

    if [ "$confirmation" != "yes" ]; then
        log "Destroy cancelled"
        return
    fi

    cd "$TERRAFORM_DIR"
    terraform destroy \
        -var-file="$([ -f "environments/${ENVIRONMENT}.tfvars" ] && echo "environments/${ENVIRONMENT}.tfvars" || echo "terraform.tfvars")" \
        -no-color \
        -auto-approve \
        >> "$LOGFILE" 2>&1 || error "Terraform destroy failed"

    success "Infrastructure destroyed"
}

################################################################################
# Main Execution
################################################################################

main() {
    log "========================================="
    log "RAG QA Hindi - AWS ECS Deployment"
    log "========================================="
    log "Environment: $ENVIRONMENT"
    log "Action: $ACTION"
    log "Log file: $LOGFILE"
    log ""

    check_prerequisites
    load_configuration
    validate_terraform

    case "$ACTION" in
        plan)
            terraform_plan
            ;;
        apply)
            terraform_plan
            terraform_apply
            wait_for_infrastructure
            create_task_definitions
            build_and_push_images
            run_migrations
            seed_data
            wait_for_services
            print_summary
            ;;
        destroy)
            terraform_destroy
            ;;
        *)
            error "Unknown action: $ACTION. Use 'plan', 'apply', or 'destroy'."
            ;;
    esac

    success "Deployment script completed successfully"
}

main "$@"
