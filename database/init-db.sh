#!/bin/bash

# init-db.sh - Initialize PostgreSQL database with migrations and seed data
# This script runs all migrations in order, then populates seed data
# Usage: ./init-db.sh [--with-seed] [--skip-seed]
# Environment variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration from environment or defaults
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-ragqa}"
POSTGRES_USER="${POSTGRES_USER:-ragqa_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Determine if we should run seed data
RUN_SEED=true
if [[ "$1" == "--skip-seed" ]]; then
    RUN_SEED=false
fi

# Function to run a migration file
run_migration() {
    local migration_file=$1
    local migration_name=$(basename "$migration_file")

    echo -e "${YELLOW}Running migration: $migration_name${NC}"

    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -f "$migration_file"; then
        echo -e "${GREEN}✓ $migration_name completed${NC}"
    else
        echo -e "${RED}✗ $migration_name failed${NC}"
        exit 1
    fi
}

# Function to run a seed file
run_seed() {
    local seed_file=$1
    local seed_name=$(basename "$seed_file")

    echo -e "${YELLOW}Seeding: $seed_name${NC}"

    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -f "$seed_file"; then
        echo -e "${GREEN}✓ $seed_name completed${NC}"
    else
        echo -e "${RED}✗ $seed_name failed${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Database Initialization Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Host: $POSTGRES_HOST"
echo "Port: $POSTGRES_PORT"
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo ""

# Check if PostgreSQL is accessible
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if ! PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL connection successful${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"
SEED_DIR="$SCRIPT_DIR/seed"

# Run migrations in order
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Running Migrations (001-014)${NC}"
echo -e "${YELLOW}========================================${NC}"
for migration_file in "$MIGRATIONS_DIR"/[0-9]*.sql; do
    if [ -f "$migration_file" ]; then
        run_migration "$migration_file"
    fi
done
echo ""

# Run seed data if requested
if [ "$RUN_SEED" = true ]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Seeding Initial Data${NC}"
    echo -e "${YELLOW}========================================${NC}"

    # Seed order matters: roles first, then users, then config
    run_seed "$SEED_DIR/seed_roles_and_permissions.sql"
    run_seed "$SEED_DIR/seed_users.sql"
    run_seed "$SEED_DIR/seed_config.sql"
    run_seed "$SEED_DIR/seed_scrape_targets.sql"
    run_seed "$SEED_DIR/seed_sample_documents.sql"
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database initialization completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
