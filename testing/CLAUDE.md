# Testing

Comprehensive test suite: integration tests (pytest), performance testing (Locust), security testing (OWASP Top 10), accessibility testing (axe-core + GIGW), UAT checklists.

## Key Files

- `scripts/run_all_tests.sh` — Run all test suites
- `tests/integration/` — E2E flows: chat, search, voice, OCR, translation, feedback
- `tests/performance/locustfile.py` — Locust load testing (100 concurrent users)
- `tests/security/` — SQL injection, JWT bypass, RBAC, rate limiting, fuzzing
- `tests/accessibility/` — WCAG 2.1 AA + GIGW (axe-core + Playwright)
- `tests/uat/checklist.md` — Manual testing checklist
- `tests/fixtures/conftest.py` — pytest fixtures, mocks

## Test Categories

### 1. Integration Tests (pytest)
E2E flows: chat → LLM, search → RAG → summary, voice → STT → LLM → TTS, OCR → extraction, translation, feedback → training trigger.
- Duration: ~2 minutes
- Command: `pytest tests/integration/`

### 2. Performance Tests (Locust)
Load testing: ramp to 100 concurrent users, 5 minutes duration.
- Target: <5s p95 latency, >50 RPS
- Metrics: response time, throughput, error rate
- Command: `locust -f tests/performance/locustfile.py`
- UI: http://localhost:8089

### 3. Security Tests (pytest)
OWASP API Top 10: SQL injection, XSS, JWT bypass, RBAC, rate limiting, PII leakage, CORS.
- Duration: ~3 minutes
- Command: `pytest tests/security/`

### 4. Accessibility Tests (pytest + axe-core)
WCAG 2.1 AA: contrast (4.5:1), ARIA labels, keyboard nav, screen reader.
GIGW: 22 Indian languages, RTL, Hindi numerals, voice nav.
- Command: `pytest tests/accessibility/`

### 5. UAT (Manual)
Functional, usability, Hindi rendering, edge cases.
- Checklist: `tests/uat/checklist.md`

## Running Tests

```bash
./scripts/run_all_tests.sh          # All tests
pytest tests/integration/ -v        # Integration (verbose)
pytest tests/security/ -k "injection" # Security (filtered)
locust -f tests/performance/locustfile.py  # Load test
```

## Benchmarks

- Chat: <2s p95
- Search: <3s p95
- Voice: <4s p95
- OCR: <5s p95
- Translation: <1s p95
- Throughput: >50 RPS

## Fixtures

- test_db (in-memory SQLite)
- mock_gateway, mock_rag_service, mock_llm_service
- auth_token (valid JWT)
- sample_document, sample_query

## Coverage

- Integration: 80% code
- Security: OWASP Top 10
- Accessibility: WCAG 2.1 AA + GIGW
- Performance: <5s p95
