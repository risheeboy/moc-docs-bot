# Performance Test Report

**Date:** {{date}}
**Environment:** {{environment}}
**Test Duration:** {{duration}}
**Total Requests:** {{total_requests}}

---

## Executive Summary

This report contains performance test results for the RAG-based Hindi QA system.

### SLA Compliance

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| p95 Latency | <5000ms | {{p95_latency}}ms | {{p95_status}} |
| p99 Latency | <10000ms | {{p99_latency}}ms | {{p99_status}} |
| Error Rate | <1% | {{error_rate}}% | {{error_status}} |
| Throughput | >100 RPS | {{throughput}} RPS | {{throughput_status}} |

---

## Endpoint Performance

### Chat Endpoint

- **Mean Latency:** {{chat_mean}}ms
- **p50:** {{chat_p50}}ms
- **p95:** {{chat_p95}}ms
- **p99:** {{chat_p99}}ms
- **Max:** {{chat_max}}ms
- **Requests:** {{chat_count}}

### Search Endpoint

- **Mean Latency:** {{search_mean}}ms
- **p50:** {{search_p50}}ms
- **p95:** {{search_p95}}ms
- **p99:** {{search_p99}}ms
- **Max:** {{search_max}}ms
- **Requests:** {{search_count}}

### Translation Endpoint

- **Mean Latency:** {{translate_mean}}ms
- **p50:** {{translate_p50}}ms
- **p95:** {{translate_p95}}ms
- **p99:** {{translate_p99}}ms
- **Max:** {{translate_max}}ms
- **Requests:** {{translate_count}}

---

## Load Test Results

### Concurrent Users: {{concurrent_users}}

**Chat Users:**
- Active: {{chat_users}}
- Success Rate: {{chat_success}}%
- Mean Response Time: {{chat_load_mean}}ms

**Search Users:**
- Active: {{search_users}}
- Success Rate: {{search_success}}%
- Mean Response Time: {{search_load_mean}}ms

**Mixed Workload:**
- Active: {{mixed_users}}
- Success Rate: {{mixed_success}}%
- Mean Response Time: {{mixed_load_mean}}ms

---

## Bottleneck Analysis

{{bottleneck_analysis}}

---

## Recommendations

{{recommendations}}

---

## Appendix: Raw Data

See attached CSV files:
- `response_time_benchmark.json`
- `locust_stats_*.csv`

