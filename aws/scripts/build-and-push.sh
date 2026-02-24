#!/bin/bash

################################################################################
# Build and Push Docker Images to ECR
# Builds all service Docker images and pushes them to AWS ECR
#
# Usage: ./build-and-push.sh [AWS_REGION] [IMAGE_TAG]
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${1:-ap-south-1}"
IMAGE_TAG="${2:-latest}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOGFILE="${SCRIPT_DIR}/build-$(date +%Y%m%d-%H%M%S).log"

# Service configurations
declare -A SERVICES=(
    ["api-gateway"]="services/api-gateway"
    ["rag-service"]="services/rag-service"
    ["llm-service"]="services/llm-service"
    ["speech-service"]="services/speech-service"
    ["translation-service"]="services/translation-service"
    ["ocr-service"]="services/ocr-service"
    ["data-ingestion"]="services/data-ingestion"
    ["model-training"]="services/model-training"
    ["chat-widget"]="services/chat-widget"
    ["search-page"]="services/search-page"
    ["admin-dashboard"]="services/admin-dashboard"
)

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

check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi

    if ! docker ps &> /dev/null; then
        error "Docker daemon is not running or you don't have permission"
    fi

    success "Docker is available"
}

check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
    fi

    success "AWS credentials verified"
}

get_ecr_token() {
    log "Getting ECR authentication token..."

    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)

    # Get ECR login token
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com" \
        >> "$LOGFILE" 2>&1 || error "Failed to authenticate with ECR"

    success "ECR authentication successful"
}

create_ecr_repositories() {
    log "Creating ECR repositories..."

    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)

    for service_name in "${!SERVICES[@]}"; do
        local repo_name="ragqa/${service_name}"

        log "Ensuring ECR repository exists: $repo_name..."

        # Create repository if it doesn't exist
        aws ecr create-repository \
            --repository-name "$repo_name" \
            --region "$AWS_REGION" \
            --encryption-configuration encryptionType=AES \
            --image-tag-mutability MUTABLE \
            --image-scanning-configuration scanOnPush=true \
            >> "$LOGFILE" 2>&1 || true  # Repository might already exist

        # Set lifecycle policy to keep last 10 images
        aws ecr put-lifecycle-policy \
            --repository-name "$repo_name" \
            --lifecycle-policy-text '{
                "rules": [
                    {
                        "rulePriority": 1,
                        "description": "Keep last 10 images",
                        "selection": {
                            "tagStatus": "any",
                            "countType": "imageCountMoreThan",
                            "countNumber": 10
                        },
                        "action": {
                            "type": "expire"
                        }
                    }
                ]
            }' \
            --region "$AWS_REGION" \
            >> "$LOGFILE" 2>&1 || true

        success "ECR repository ready: $repo_name"
    done
}

build_service_image() {
    local service_name="$1"
    local service_path="${SERVICES[$service_name]}"
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)

    local full_repo_name="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/ragqa/${service_name}"
    local dockerfile_path="${PROJECT_ROOT}/${service_path}/Dockerfile"

    log "Building Docker image for: $service_name..."

    if [ ! -d "${PROJECT_ROOT}/${service_path}" ]; then
        warning "Service directory not found: ${PROJECT_ROOT}/${service_path}. Skipping..."
        return 0
    fi

    if [ ! -f "$dockerfile_path" ]; then
        warning "Dockerfile not found: $dockerfile_path. Skipping..."
        return 0
    fi

    # Build the Docker image
    docker build \
        --file "$dockerfile_path" \
        --tag "${full_repo_name}:${IMAGE_TAG}" \
        --tag "${full_repo_name}:latest" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        "${PROJECT_ROOT}/${service_path}" \
        >> "$LOGFILE" 2>&1 || error "Failed to build Docker image for: $service_name"

    success "Built Docker image: ${full_repo_name}:${IMAGE_TAG}"
}

push_service_image() {
    local service_name="$1"
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)

    local full_repo_name="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com/ragqa/${service_name}"

    log "Pushing Docker image to ECR: $service_name..."

    # Push both tags
    docker push "${full_repo_name}:${IMAGE_TAG}" >> "$LOGFILE" 2>&1 || error "Failed to push tag $IMAGE_TAG for: $service_name"
    docker push "${full_repo_name}:latest" >> "$LOGFILE" 2>&1 || error "Failed to push tag latest for: $service_name"

    success "Pushed Docker image: ${full_repo_name}:${IMAGE_TAG}"
}

build_all_services() {
    log "Building all service images..."

    for service_name in "${!SERVICES[@]}"; do
        build_service_image "$service_name"
    done

    success "All service images built successfully"
}

push_all_services() {
    log "Pushing all service images to ECR..."

    for service_name in "${!SERVICES[@]}"; do
        push_service_image "$service_name"
    done

    success "All service images pushed to ECR successfully"
}

print_summary() {
    local aws_account_id
    aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local registry="${aws_account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    log "========================================="
    log "BUILD AND PUSH SUMMARY"
    log "========================================="

    echo ""
    echo -e "${GREEN}Images built and pushed:${NC}"
    for service_name in "${!SERVICES[@]}"; do
        echo "  - ${registry}/ragqa/${service_name}:${IMAGE_TAG}"
    done

    echo ""
    echo -e "${YELLOW}Log file:${NC} $LOGFILE"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    log "========================================="
    log "Build and Push Docker Images to ECR"
    log "========================================="
    log "AWS Region: $AWS_REGION"
    log "Image Tag: $IMAGE_TAG"
    log "Log file: $LOGFILE"
    log ""

    check_docker
    check_aws_credentials
    get_ecr_token
    create_ecr_repositories
    build_all_services
    push_all_services
    print_summary

    success "Build and push completed successfully"
}

main "$@"
