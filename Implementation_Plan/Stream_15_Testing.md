### STREAM 15: Integration Testing, Performance Testing & Security Scanning (**NEW**)

**Agent Goal:** Build the end-to-end integration test suite, load/performance testing framework, and automated security scanning. (Requirements pages 12-13 list test reports — UAT, performance, security — as mandatory deliverables. Pages 22-23 specify security audit requirements.)

**Files to create:**
```
testing/
├── Dockerfile                       # python:3.11-slim + test tools
├── requirements.txt
├── integration/
│   ├── conftest.py                  # Docker Compose test fixtures (spin up all services)
│   ├── test_e2e_chat_flow.py        # Upload doc → ingest → ask question → get answer + sources
│   ├── test_e2e_search_flow.py      # Scrape page → ingest → semantic search → AI summary
│   ├── test_e2e_voice_flow.py       # Audio in → STT → query → response → TTS → audio out
│   ├── test_e2e_ocr_flow.py         # Upload scanned Hindi PDF → OCR → ingest → query
│   ├── test_e2e_translation.py      # Query in Hindi → translate → respond in English
│   ├── test_e2e_feedback.py         # Submit feedback → sentiment analysis → dashboard
│   ├── test_cross_service_health.py # All services healthy and communicating
│   └── test_document_lifecycle.py   # Upload → ingest → query → delete → verify removed from Milvus
├── performance/
│   ├── locustfile.py                # Locust load testing: chat, search, voice endpoints
│   ├── scenarios/
│   │   ├── chat_load.py             # Concurrent chat sessions (target: <5s p95)
│   │   ├── search_load.py           # Concurrent search queries
│   │   ├── voice_load.py            # Concurrent STT/TTS requests
│   │   └── mixed_load.py            # Realistic mixed traffic pattern
│   ├── benchmarks/
│   │   ├── response_time_benchmark.py  # Measure p50/p95/p99 latency per endpoint
│   │   └── throughput_benchmark.py     # Max requests/sec per service
│   └── report_generator.py         # Generate performance test report
├── security/
│   ├── run_security_scan.sh         # Orchestrate all security checks
│   ├── api_security_test.py         # OWASP API Top 10 checks (injection, auth bypass, etc.)
│   ├── input_fuzzer.py              # Fuzz all API inputs (XSS, SQL injection, Hindi Unicode attacks)
│   ├── auth_test.py                 # JWT bypass attempts, privilege escalation tests
│   ├── rate_limit_test.py           # Verify rate limiting works under load
│   ├── ssl_check.py                 # TLS configuration validation
│   ├── dependency_audit.sh          # pip-audit + npm audit for known CVEs
│   ├── license_audit.sh            # SBOM generation + license compatibility check (all deps)
│   ├── container_scan.sh           # Container image vulnerability scanning (trivy/grype)
│   └── report_generator.py         # Generate security audit report
├── uat/
│   ├── test_accessibility_wcag.py   # Automated WCAG 2.1 AA checks (axe-core via Playwright)
│   ├── test_accessibility_gigw.py   # GIGW compliance checks (Indian govt website guidelines)
│   ├── test_hindi_rendering.py      # Verify Devanagari rendering, fonts, ligatures in UI
│   ├── test_multilingual_ui.py      # Verify all UI strings translated correctly
│   └── test_browser_compatibility.py # Chrome, Firefox, Edge, Safari, mobile viewports
├── scripts/
│   ├── run_all_tests.sh
│   ├── run_integration.sh
│   ├── run_performance.sh
│   ├── run_security.sh
│   └── run_uat.sh
└── reports/
    ├── .gitkeep                     # Generated test reports go here
    └── templates/
        ├── performance_report.md
        ├── security_audit_report.md
        └── uat_report.md
```

**Key test categories (from Requirements pages 12-13, 22-23):**
- **Integration tests:** End-to-end flows across all services via Docker Compose
- **Performance tests:** Locust-based load testing targeting <5s p95 response time, concurrent user simulation
- **Security tests:** OWASP API Top 10, input fuzzing (including Hindi Unicode edge cases), JWT auth testing, dependency CVE audit, TLS validation
- **UAT tests:** WCAG 2.1 AA automated checks (axe-core), **GIGW compliance** (Guidelines for Indian Government Websites), Hindi rendering, browser compatibility
- **Report generation:** Auto-generated test reports in markdown (deliverables for Ministry)

**Depends on:** All other streams complete (runs against deployed services).

---

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: tests must call services at the exact ports defined in §1
- §4 Error Response Format: validate all services return errors in the exact format from §4
- §5 Health Check Format: validate all services return health in the exact format from §5
- §8 Inter-Service Contracts: integration tests should validate request/response schemas from §8.1-8.7
- §12 RBAC: security tests must verify all 4 roles have correct access per §12
- §13 Chatbot Fallback: test that low-confidence responses trigger exact fallback messages from §13

---

## Agent Prompt

### Agent 15: Integration, Performance & Security Testing (**NEW**)
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Tests must validate contracts from §4 (errors), §5 (health), §8 (API schemas), §12 (RBAC).

Build comprehensive test suite (runs against fully deployed system):
INTEGRATION: E2E tests for chat flow, search flow, voice flow, OCR flow,
  translation flow, feedback→sentiment flow, document lifecycle (upload→ingest→
  query→delete→verify removed from Milvus).
PERFORMANCE: Locust load tests targeting <5s p95 response time. Scenarios:
  concurrent chat, concurrent search, concurrent voice, mixed realistic traffic.
  Throughput benchmarks per service.
SECURITY: OWASP API Top 10 checks, input fuzzing (including Hindi Unicode edge
  cases), JWT auth bypass attempts, rate limit verification, TLS 1.2+ validation,
  dependency CVE audit (pip-audit + npm audit), container image scanning
  (trivy/grype), license audit (SBOM generation + compatibility check).
UAT: Automated WCAG 2.1 AA checks (axe-core via Playwright), GIGW compliance
  checks, Hindi Devanagari rendering tests, browser compatibility tests.
Auto-generate test reports (performance, security audit, UAT) in markdown.
```

