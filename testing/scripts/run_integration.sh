#!/bin/bash
# Run integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$TESTING_DIR/reports"

mkdir -p "$REPORTS_DIR"

echo "Running integration tests..."
echo "Target: http://localhost:8000"
echo ""

# Run pytest with detailed output
python -m pytest \
  "$TESTING_DIR/integration/" \
  -v \
  --tb=short \
  --junit-xml="$REPORTS_DIR/integration_results.xml" \
  --html="$REPORTS_DIR/integration_report.html" \
  --self-contained-html \
  --cov="$TESTING_DIR/integration" \
  --cov-report=html:"$REPORTS_DIR/integration_coverage" \
  --cov-report=term \
  -m integration \
  --timeout=30 \
  --maxfail=10 \
  2>&1 | tee "$REPORTS_DIR/integration.log"

echo ""
echo "Integration tests completed."
echo "Report: $REPORTS_DIR/integration_report.html"
