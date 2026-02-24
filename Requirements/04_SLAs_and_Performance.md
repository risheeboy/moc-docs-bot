# SLAs and Performance Requirements

**Source:** Requirements.pdf pages 11-12

## Performance Targets

| Metric | Target | Notes |
|---|---|---|
| Response time (p95) | < 5 seconds | For chatbot and search queries |
| System uptime | 99.5% | Measured monthly |
| Concurrent users | Not explicitly specified | Must handle realistic traffic for government website |
| Throughput | Must scale to meet demand | Per-service throughput benchmarks required |

## Service Level Agreements

### Uptime & Availability
- **99.5% uptime** SLA for production system
- Measured on a monthly basis
- Planned maintenance windows excluded (must be pre-communicated)
- Health checks and automatic container restart for self-healing

### Response Time
- **< 5 seconds p95** for end-to-end query response (user query → AI response)
- This includes: API Gateway processing, RAG retrieval, LLM inference, any translation
- Performance must be maintained under concurrent load

### Support & Maintenance
- **3-year Annual Maintenance Contract (AMC)** after initial deployment
- Support coverage: business hours (9 AM - 6 PM IST) minimum
- Bug fix SLAs:
  - Critical bugs: resolution within 24 hours
  - Major bugs: resolution within 72 hours
  - Minor bugs: resolution within 1 week
- Software updates and security patches included in AMC
- Model retraining and performance optimization included

## Monitoring & Alerting Requirements

- Real-time monitoring dashboards (Grafana)
- Automated alerts for:
  - Service downtime
  - Response time degradation (> 5s p95)
  - Error rate spikes
  - GPU memory / utilization alerts
  - Storage capacity warnings
  - Failed backup alerts
- Monthly performance reports for Ministry stakeholders

## Load Testing Requirements

- Load tests must simulate realistic concurrent usage patterns
- Test scenarios:
  - Concurrent chat sessions
  - Concurrent search queries
  - Concurrent voice (STT/TTS) requests
  - Mixed realistic traffic patterns
- Results must demonstrate < 5s p95 compliance under load
- Load test reports are a **mandatory deliverable**
