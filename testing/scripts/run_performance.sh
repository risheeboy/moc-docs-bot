#!/bin/bash
# Run performance and load tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$TESTING_DIR/reports"

mkdir -p "$REPORTS_DIR"

echo "Running performance tests..."
echo "Target: http://localhost:8000"
echo ""

# Run response time benchmarks
echo "[1/3] Response time benchmarks..."
cd "$TESTING_DIR/performance/benchmarks"
python response_time_benchmark.py 2>&1 | tee "$REPORTS_DIR/response_time_benchmark.log"

echo ""

# Run throughput benchmarks (if available)
if [ -f "$TESTING_DIR/performance/benchmarks/throughput_benchmark.py" ]; then
    echo "[2/3] Throughput benchmarks..."
    python throughput_benchmark.py 2>&1 | tee "$REPORTS_DIR/throughput_benchmark.log"
else
    echo "[2/3] Throughput benchmarks (skipped - not implemented)"
fi

echo ""

# Run Locust load tests (headless, brief test)
echo "[3/3] Locust load tests..."
if command -v locust &> /dev/null; then
    cd "$TESTING_DIR/performance"
    locust \
      -f locustfile.py \
      --headless \
      -u 20 \
      -r 5 \
      -t 2m \
      -H http://localhost:8000 \
      --csv="$REPORTS_DIR/locust_stats" \
      ChatUser MixedUser \
      2>&1 | tee "$REPORTS_DIR/locust_test.log" || true

    echo ""
    echo "Locust CSV stats:"
    ls -lh "$REPORTS_DIR/locust_stats"* 2>/dev/null || echo "(No CSV files)"
else
    echo "[3/3] Locust not installed - skipping"
fi

echo ""
echo "Performance tests completed."
echo "Reports in: $REPORTS_DIR/"
