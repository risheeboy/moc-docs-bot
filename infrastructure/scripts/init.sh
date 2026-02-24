#!/bin/bash
# ============================================================================
# Infrastructure Initialization Script
# RAG-Based Hindi QA System - First-Time Setup
# ============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo "=========================================="
echo "RAG-QA System - Infrastructure Init"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo ""

# ============================================================================
# 1. VERIFY PREREQUISITES
# ============================================================================
echo "[1/6] Verifying prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi
echo "✓ Docker: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi
echo "✓ Docker Compose: $(docker-compose --version)"

# Check NVIDIA Docker runtime (if GPUs present)
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA GPU detected"
    NVIDIA_DRIVER=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
    CUDA_VERSION=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1)
    echo "  - Driver Version: $NVIDIA_DRIVER"
    echo "  - CUDA Compute Capability: $CUDA_VERSION"

    # Verify nvidia-container-toolkit
    if ! docker run --rm --runtime=nvidia nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo "  WARNING: nvidia-container-toolkit may not be properly configured"
        echo "  Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html"
    else
        echo "✓ NVIDIA Container Toolkit is working"
    fi
else
    echo "⚠ No NVIDIA GPU detected - CPU-only mode"
fi

echo ""

# ============================================================================
# 2. SETUP ENVIRONMENT FILE
# ============================================================================
echo "[2/6] Setting up environment configuration..."

if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "  .env file already exists"
else
    if [ -f "$PROJECT_ROOT/infrastructure/.env.example" ]; then
        cp "$PROJECT_ROOT/infrastructure/.env.example" "$PROJECT_ROOT/.env"
        echo "✓ Created .env from template"
        echo "  WARNING: Update .env with production values before deploying!"
    else
        echo "  ERROR: .env.example not found"
        exit 1
    fi
fi

echo ""

# ============================================================================
# 3. CREATE NAMED VOLUMES
# ============================================================================
echo "[3/6] Creating Docker volumes..."

VOLUMES=(
    "postgres-data"
    "langfuse-pg-data"
    "milvus-data"
    "etcd-data"
    "redis-data"
    "minio-data"
    "model-cache"
    "uploaded-docs"
    "grafana-data"
    "prometheus-data"
    "langfuse-data"
    "loki-data"
    "backup-data"
)

for volume in "${VOLUMES[@]}"; do
    if docker volume ls | grep -q "^${volume}"; then
        echo "  Volume '$volume' already exists"
    else
        docker volume create "$volume"
        echo "✓ Created volume: $volume"
    fi
done

echo ""

# ============================================================================
# 4. BUILD CUSTOM IMAGES
# ============================================================================
echo "[4/6] Building custom Docker images..."

cd "$PROJECT_ROOT"

# Build NGINX image
echo "  Building NGINX image..."
if docker build -f infrastructure/nginx/Dockerfile -t rag-qa-nginx:latest infrastructure/nginx/ &> /dev/null; then
    echo "✓ Built: rag-qa-nginx:latest"
else
    echo "  WARNING: Failed to build NGINX image (services may not start)"
fi

echo ""

# ============================================================================
# 5. INITIALIZE POSTGRES SCHEMA
# ============================================================================
echo "[5/6] Preparing PostgreSQL initialization script..."

cat > "$PROJECT_ROOT/infrastructure/scripts/init-postgres.sql" << 'EOF'
-- Initialize RAG-QA Database
CREATE SCHEMA IF NOT EXISTS ragqa;
GRANT ALL PRIVILEGES ON SCHEMA ragqa TO ragqa_user;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create audit log table
CREATE TABLE IF NOT EXISTS ragqa.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    user_id UUID,
    status VARCHAR(50),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_service ON ragqa.audit_log(service_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON ragqa.audit_log(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ragqa TO ragqa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ragqa TO ragqa_user;
EOF

echo "✓ Created PostgreSQL init script"

echo ""

# ============================================================================
# 6. VERIFY NETWORK
# ============================================================================
echo "[6/6] Setting up Docker network..."

NETWORK_NAME="rag-network"
if docker network ls | grep -q "^${NETWORK_NAME}"; then
    echo "  Network '$NETWORK_NAME' already exists"
else
    docker network create --driver bridge --subnet 172.28.0.0/16 "$NETWORK_NAME"
    echo "✓ Created network: $NETWORK_NAME"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "=========================================="
echo "✓ Infrastructure initialization complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with production values"
echo "2. Generate SSL certificates:"
echo "   mkdir -p infrastructure/nginx/ssl"
echo "   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\"
echo "     -keyout infrastructure/nginx/ssl/key.pem \\"
echo "     -out infrastructure/nginx/ssl/cert.pem"
echo "3. Start services: ./infrastructure/scripts/start.sh"
echo "4. Check health: ./infrastructure/scripts/health-check.sh"
echo ""
