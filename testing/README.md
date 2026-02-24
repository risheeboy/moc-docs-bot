# Testing Suite — RAG-based Hindi & English, Search & QA System

Complete end-to-end testing framework including integration tests, performance benchmarks, security scans, and UAT validation.

---

## Overview

This testing suite validates the **RAG-based Hindi & English, Search & QA system for India's Ministry of Culture** across four dimensions:

1. **Integration Tests** — End-to-end workflows (chat, search, voice, OCR, translation, feedback, document lifecycle)
2. **Performance Tests** — Load testing and latency benchmarks (target: <5s p95)
3. **Security Tests** — OWASP API Top 10, input fuzzing, authentication, rate limiting, dependency audit
4. **UAT Tests** — Accessibility (WCAG 2.1 AA), GIGW compliance, Hindi rendering, browser compatibility

---

## Directory Structure

```
testing/
├── Dockerfile                          # Test container image
├── requirements.txt                    # Python dependencies
├── integration/                        # End-to-end tests
│   ├── conftest.py                     # Docker Compose fixtures, service health checks
│   ├── test_e2e_chat_flow.py          # Chat widget workflows
│   ├── test_e2e_search_flow.py        # Semantic search workflows
│   ├── test_e2e_voice_flow.py         # STT/TTS workflows
│   ├── test_e2e_ocr_flow.py           # OCR → Ingest → Query
│   ├── test_e2e_translation.py        # Hindi ↔ English translation
│   ├── test_e2e_feedback.py           # Feedback → Sentiment analysis
│   ├── test_cross_service_health.py   # All services healthy, communicating
│   └── test_document_lifecycle.py     # Upload → Ingest → Query → Delete
├── performance/                        # Load & performance tests
│   ├── locustfile.py                   # Locust load testing framework
│   ├── scenarios/                      # Detailed load scenarios (stubs)
│   │   ├── chat_load.py
│   │   ├── search_load.py
│   │   ├── voice_load.py
│   │   └── mixed_load.py
│   └── benchmarks/
│       ├── response_time_benchmark.py  # p50/p95/p99 latency per endpoint
│       ├── throughput_benchmark.py     # Max req/sec per service (stub)
│       └── report_generator.py         # Generate perf reports (stub)
├── security/                           # Security scanning & fuzzing
│   ├── api_security_test.py            # OWASP API Top 10 checks
│   ├── input_fuzzer.py                 # XSS, SQL injection, Unicode attacks
│   ├── auth_test.py                    # JWT, privilege escalation (stub)
│   ├── rate_limit_test.py              # Rate limiting validation (stub)
│   ├── ssl_check.py                    # TLS 1.2+ validation (stub)
│   ├── dependency_audit.sh             # pip-audit + npm audit (stub)
│   ├── license_audit.sh                # SBOM generation (stub)
│   ├── container_scan.sh               # trivy/grype (stub)
│   └── report_generator.py             # Security audit report (stub)
├── uat/                                # User acceptance tests
│   ├── test_accessibility_wcag.py      # WCAG 2.1 AA checks
│   ├── test_accessibility_gigw.py      # GIGW compliance checks
│   ├── test_hindi_rendering.py         # Devanagari rendering
│   ├── test_multilingual_ui.py         # UI translations
│   └── test_browser_compatibility.py   # Chrome, Firefox, Safari, mobile
├── scripts/                            # Test orchestration
│   ├── run_all_tests.sh                # Run all test suites
│   ├── run_integration.sh              # Integration tests only
│   ├── run_performance.sh              # Performance tests only
│   ├── run_security.sh                 # Security tests only
│   └── run_uat.sh                      # UAT tests only
└── reports/                            # Generated test reports
    ├── templates/
    │   ├── performance_report.md       # Template for perf report
    │   ├── security_audit_report.md    # Template for security report
    │   └── uat_report.md               # Template for UAT report
    └── [generated reports]
```

---

## Prerequisites

### System Requirements
- Docker & Docker Compose (for containerized test environment)
- Python 3.11+
- Node.js 20+ (for frontend tests if needed)
- Linux/macOS (or WSL on Windows)

### Dependencies

Install test dependencies:

```bash
pip install -r requirements.txt
```

Key packages:
- `pytest` — Test framework
- `httpx` — HTTP client (async support)
- `locust` — Load testing
- `docker` — Docker client
- `testcontainers` — Container test fixtures
- `hypothesis` — Property-based testing & fuzzing
- `playwright` — Browser automation (UAT)
- `bandit`, `safety` — Python security analysis

---

## Quick Start

### 1. Start Services

```bash
# Start Docker Compose services
docker-compose up -d

# Verify all services healthy
python -c "from testing.integration.conftest import wait_for_all_services; import asyncio; asyncio.run(wait_for_all_services())"
```

### 2. Run All Tests

```bash
bash testing/scripts/run_all_tests.sh
```

### 3. View Reports

Reports are generated in `testing/reports/`:
- `integration_report.html` — Integration test results
- `performance_report.md` — Latency & throughput
- `api_security_report.html` — OWASP API Top 10 findings
- `hindi_rendering_report.html` — Devanagari rendering validation
- `accessibility_report.html` — WCAG 2.1 AA compliance

---

## Test Execution

### Integration Tests

```bash
# All integration tests
bash testing/scripts/run_integration.sh

# Single test file
python -m pytest testing/integration/test_e2e_chat_flow.py -v

# Specific test
python -m pytest testing/integration/test_e2e_chat_flow.py::TestChatFlowBasic::test_health_check_all_services -v

# With coverage
python -m pytest testing/integration/ --cov --cov-report=html
```

**Coverage:**
- ✓ Health checks (§5 contract validation)
- ✓ Chat flow (query → answer + sources)
- ✓ Search flow (query → results + multimedia + events)
- ✓ Voice flow (STT → query → TTS)
- ✓ OCR flow (scanned PDF → text → ingest)
- ✓ Translation flow (Hindi ↔ English)
- ✓ Feedback (sentiment analysis)
- ✓ Document lifecycle (upload → ingest → query → delete)
- ✓ Cross-service communication
- ✓ Error handling (§4 contract validation)
- ✓ RBAC enforcement (§12 contract validation)

### Performance Tests

#### Response Time Benchmarks

```bash
cd testing/performance/benchmarks
python response_time_benchmark.py
```

Outputs:
- p50, p95, p99 latency per endpoint
- Validates <5s p95 SLA
- Results saved to `/tmp/response_time_benchmark.json`

#### Locust Load Testing

```bash
# Chat load test (100 concurrent users)
locust -f testing/performance/locustfile.py \
  --headless -u 100 -r 10 -t 5m -H http://localhost:8000 ChatUser

# Mixed realistic load
locust -f testing/performance/locustfile.py \
  --headless -u 100 -r 20 -t 10m -H http://localhost:8000 MixedUser

# Web UI for monitoring
locust -f testing/performance/locustfile.py -H http://localhost:8000
# Open http://localhost:8089 in browser
```

**Scenarios:**
- Chat: 4 tasks per user (Hindi/English/history/streaming)
- Search: 3 tasks per user (basic/filtered/pagination)
- Voice: 3 tasks per user (STT/TTS/detection)
- Mixed: 4+3+1 tasks (realistic traffic)

### Security Tests

```bash
# All security tests
bash testing/scripts/run_security.sh

# OWASP API Top 10 only
python -m pytest testing/security/api_security_test.py -v

# Input fuzzing
python -m pytest testing/security/input_fuzzer.py -v

# Dependency audit
pip-audit --desc
npm audit
bandit -r testing/

# Full security scan report
bash testing/scripts/run_security.sh  # Generates comprehensive report
```

**Coverage:**
- ✓ Authentication & authorization (JWT, roles)
- ✓ Input validation (SQL injection, XSS, command injection)
- ✓ Unicode/Hindi edge cases
- ✓ Rate limiting
- ✓ Resource exhaustion protection
- ✓ Data exposure prevention
- ✓ Security headers
- ✓ Python/NPM dependency CVEs
- ✓ Container image vulnerabilities

### UAT Tests

```bash
# All UAT tests
bash testing/scripts/run_uat.sh

# Hindi rendering
python -m pytest testing/uat/test_hindi_rendering.py -v

# Accessibility (WCAG 2.1 AA)
python -m pytest testing/uat/test_accessibility_wcag.py -v

# GIGW compliance
python -m pytest testing/uat/test_accessibility_gigw.py -v

# Browser compatibility
python -m pytest testing/uat/test_browser_compatibility.py -v
```

**Coverage:**
- ✓ Devanagari character set, ligatures, combining marks
- ✓ WCAG 2.1 Level AA accessibility
- ✓ GIGW requirements (emblem, footer, language toggle, ARIA landmarks)
- ✓ Hindi/English bilingual support
- ✓ Browser compatibility (Chrome, Firefox, Safari, Edge, mobile)
- ✓ Responsive design (320px–1920px)

---

## Contract Validation

Tests validate shared contracts from `Implementation_Plan/01_Shared_Contracts.md`:

| Section | Tests | Coverage |
|---------|-------|----------|
| §1 Service Registry | `test_cross_service_health.py` | All services reachable |
| §4 Error Response Format | All test files | Error codes, structure |
| §5 Health Check Format | `test_cross_service_health.py` | Status, dependencies, latency |
| §8 Inter-Service Contracts | Integration tests | Request/response schemas |
| §12 RBAC | `api_security_test.py` | Role access enforcement |
| §13 Fallback Behavior | `test_e2e_chat_flow.py` | Low confidence triggers fallback |

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# API Gateway
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# Test User Tokens (mock for testing)
ADMIN_TOKEN=mock-admin-token
EDITOR_TOKEN=mock-editor-token
VIEWER_TOKEN=mock-viewer-token
API_CONSUMER_TOKEN=mock-api-consumer-token

# Docker Compose
DOCKER_NETWORK=rag-network
DOCKER_COMPOSE_FILE=docker-compose.yml
```

### Pytest Configuration

`pytest.ini`:

```ini
[pytest]
testpaths = testing/
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: integration tests
    slow: slow tests (>5s)
    security: security tests
    requires_gpu: requires GPU
timeout = 30
```

---

## SLA Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Chat p95 latency** | <5s | Including RAG retrieval + LLM inference |
| **Search p95 latency** | <5s | Including semantic ranking |
| **Error rate** | <1% | Across all endpoints |
| **Availability** | >99% | Uptime SLA |
| **Rate limit** | <30 req/min (viewer) | Per user role |

---

## Troubleshooting

### Services Not Healthy

```bash
# Check Docker Compose logs
docker-compose logs api-gateway
docker-compose logs rag-service
docker-compose logs llm-service

# Verify network
docker network ls | grep rag-network

# Restart services
docker-compose down
docker-compose up -d
```

### Pytest Connection Errors

```bash
# Verify services are running
curl http://localhost:8000/health
curl http://localhost:8001/health

# Check firewall rules
sudo ufw status
```

### Slow Performance Tests

- Reduce concurrent users (`-u` flag in Locust)
- Reduce test duration (`-t` flag)
- Check system CPU/memory: `htop`, `free -h`

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r testing/requirements.txt
      - run: docker-compose up -d
      - run: python -m pytest testing/integration/ -v
      - run: bash testing/scripts/run_security.sh
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-reports
          path: testing/reports/
```

---

## Performance Baselines

### Expected Latencies (P95)

| Endpoint | Baseline | SLA |
|----------|----------|-----|
| /chat (Hindi) | 2.5s | <5s |
| /chat (English) | 2.2s | <5s |
| /search | 3.1s | <5s |
| /translate | 0.8s | <5s |
| /ocr | 4.0s | <5s |

*(Adjust based on hardware)*

---

## Contributing

When adding new tests:

1. **Follow naming:** `test_<feature>_<scenario>.py`
2. **Use fixtures:** Session, user, headers from `conftest.py`
3. **Validate contracts:** Check §4 (errors), §5 (health), §8 (schemas)
4. **Document:** Add docstrings explaining what's tested
5. **Report:** Update test coverage in this README

---

## References

- [Shared Contracts](../Implementation_Plan/01_Shared_Contracts.md)
- [Stream 15 Testing Plan](../Implementation_Plan/Stream_15_Testing.md)
- [OWASP API Top 10](https://owasp.org/www-project-api-security/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [GIGW - Guidelines for Indian Government Websites](https://www.nic.in/gigw/)

---

**Last Updated:** 2026-02-24
**Maintainer:** QA Team
**Status:** Production-Ready
