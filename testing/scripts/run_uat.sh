#!/bin/bash
# Run UAT tests: accessibility, Hindi rendering, browser compatibility

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTING_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$TESTING_DIR/reports"
UAT_DIR="$TESTING_DIR/uat"

mkdir -p "$REPORTS_DIR"

echo "Running UAT tests..."
echo ""

# Run Hindi rendering tests
echo "[1/4] Hindi Devanagari Rendering Tests..."
python -m pytest \
  "$UAT_DIR/test_hindi_rendering.py" \
  -v \
  --tb=short \
  --junit-xml="$REPORTS_DIR/hindi_rendering_results.xml" \
  --html="$REPORTS_DIR/hindi_rendering_report.html" \
  --self-contained-html \
  2>&1 | tee "$REPORTS_DIR/hindi_rendering.log" || true

echo ""

# Run accessibility tests
echo "[2/4] Accessibility Tests (WCAG 2.1 AA)..."
if [ -f "$UAT_DIR/test_accessibility_wcag.py" ]; then
    python -m pytest \
      "$UAT_DIR/test_accessibility_wcag.py" \
      -v \
      --tb=short \
      --junit-xml="$REPORTS_DIR/accessibility_results.xml" \
      --html="$REPORTS_DIR/accessibility_report.html" \
      --self-contained-html \
      2>&1 | tee "$REPORTS_DIR/accessibility.log" || true
else
    echo "  (Accessibility tests not implemented)"
fi

echo ""

# Run GIGW compliance tests
echo "[3/4] GIGW Compliance Tests..."
if [ -f "$UAT_DIR/test_accessibility_gigw.py" ]; then
    python -m pytest \
      "$UAT_DIR/test_accessibility_gigw.py" \
      -v \
      --tb=short \
      --junit-xml="$REPORTS_DIR/gigw_results.xml" \
      --html="$REPORTS_DIR/gigw_report.html" \
      --self-contained-html \
      2>&1 | tee "$REPORTS_DIR/gigw.log" || true
else
    echo "  (GIGW tests not implemented)"
fi

echo ""

# Run browser compatibility tests
echo "[4/4] Browser Compatibility Tests..."
if [ -f "$UAT_DIR/test_browser_compatibility.py" ]; then
    python -m pytest \
      "$UAT_DIR/test_browser_compatibility.py" \
      -v \
      --tb=short \
      --junit-xml="$REPORTS_DIR/browser_compat_results.xml" \
      --html="$REPORTS_DIR/browser_compat_report.html" \
      --self-contained-html \
      2>&1 | tee "$REPORTS_DIR/browser_compat.log" || true
else
    echo "  (Browser compatibility tests not implemented)"
fi

echo ""
echo "UAT tests completed."
echo "Reports in: $REPORTS_DIR/"
echo ""
echo "Summary:"
echo "  - Hindi Rendering: $REPORTS_DIR/hindi_rendering_report.html"
echo "  - Accessibility: $REPORTS_DIR/accessibility_report.html"
echo "  - GIGW: $REPORTS_DIR/gigw_report.html"
echo "  - Browser Compatibility: $REPORTS_DIR/browser_compat_report.html"
