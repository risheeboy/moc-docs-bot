#!/bin/bash
# Run security tests and scans

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$TESTING_DIR/reports"
SECURITY_DIR="$TESTING_DIR/security"

mkdir -p "$REPORTS_DIR"

echo "Running security tests..."
echo ""

# Run API security tests
echo "[1/5] API Security Tests (OWASP Top 10)..."
python -m pytest \
  "$SECURITY_DIR/api_security_test.py" \
  -v \
  --tb=short \
  --junit-xml="$REPORTS_DIR/api_security_results.xml" \
  --html="$REPORTS_DIR/api_security_report.html" \
  --self-contained-html \
  2>&1 | tee "$REPORTS_DIR/api_security.log" || true

echo ""

# Run input fuzzing tests
echo "[2/5] Input Fuzzing Tests..."
python -m pytest \
  "$SECURITY_DIR/input_fuzzer.py" \
  -v \
  --tb=short \
  --junit-xml="$REPORTS_DIR/fuzzing_results.xml" \
  --html="$REPORTS_DIR/fuzzing_report.html" \
  --self-contained-html \
  2>&1 | tee "$REPORTS_DIR/fuzzing.log" || true

echo ""

# Run dependency audit
echo "[3/5] Dependency Security Audit (pip-audit)..."
pip-audit --desc --format json --output "$REPORTS_DIR/pip_audit.json" || true
pip-audit --desc 2>&1 | tee "$REPORTS_DIR/pip_audit.txt" || true

echo ""

# Run npm audit if package.json exists
echo "[4/5] NPM Dependency Audit..."
if [ -f "$TESTING_DIR/../frontend/package.json" ]; then
    cd "$TESTING_DIR/../frontend"
    npm audit --json > "$REPORTS_DIR/npm_audit.json" || true
    npm audit 2>&1 | tee "$REPORTS_DIR/npm_audit.txt" || true
else
    echo "  (No package.json found)"
fi

echo ""

# Run bandit for code security analysis
echo "[5/5] Python Code Security Analysis (bandit)..."
if command -v bandit &> /dev/null; then
    bandit -r "$TESTING_DIR" \
      --format json \
      --output "$REPORTS_DIR/bandit_report.json" || true
    bandit -r "$TESTING_DIR" \
      --format txt \
      2>&1 | tee "$REPORTS_DIR/bandit_report.txt" || true
else
    echo "  (bandit not installed)"
fi

echo ""
echo "Security tests completed."
echo "Reports in: $REPORTS_DIR/"
echo ""
echo "Summary:"
echo "  - API Security: $REPORTS_DIR/api_security_report.html"
echo "  - Fuzzing: $REPORTS_DIR/fuzzing_report.html"
echo "  - Pip Audit: $REPORTS_DIR/pip_audit.txt"
echo "  - Bandit: $REPORTS_DIR/bandit_report.txt"
