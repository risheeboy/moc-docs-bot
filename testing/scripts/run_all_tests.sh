#!/bin/bash
# Run all tests: integration, performance, security, UAT

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$TESTING_DIR")"

echo "=========================================="
echo "RAG-QA Testing Suite"
echo "=========================================="
echo ""

# Create reports directory
mkdir -p "$TESTING_DIR/reports"

# Run integration tests
echo "[1/4] Running integration tests..."
bash "$SCRIPT_DIR/run_integration.sh" || true

# Run performance tests
echo ""
echo "[2/4] Running performance tests..."
bash "$SCRIPT_DIR/run_performance.sh" || true

# Run security tests
echo ""
echo "[3/4] Running security tests..."
bash "$SCRIPT_DIR/run_security.sh" || true

# Run UAT tests
echo ""
echo "[4/4] Running UAT tests..."
bash "$SCRIPT_DIR/run_uat.sh" || true

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Reports generated in: $TESTING_DIR/reports/"
ls -lh "$TESTING_DIR/reports/" 2>/dev/null || echo "(No reports generated)"

echo ""
echo "Done!"
