"""
Response time benchmarking for all API endpoints.
Measures p50/p95/p99 latency and validates SLA compliance (<5s p95).
"""

import asyncio
import time
import statistics
from typing import Dict, List
import httpx
import json


# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"
AUTH_HEADERS = {
    "Authorization": "Bearer mock-token",
    "Content-Type": "application/json",
}

ENDPOINTS = {
    "chat_hindi": {
        "method": "POST",
        "path": "/api/v1/chat",
        "payload": {
            "query": "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
            "language": "hi",
            "session_id": "benchmark-session",
            "chat_history": [],
        },
        "warmup": 2,
        "iterations": 10,
        "timeout": 30.0,
    },
    "chat_english": {
        "method": "POST",
        "path": "/api/v1/chat",
        "payload": {
            "query": "Tell me about Ministry of Culture",
            "language": "en",
            "session_id": "benchmark-session",
            "chat_history": [],
        },
        "warmup": 2,
        "iterations": 10,
        "timeout": 30.0,
    },
    "search": {
        "method": "POST",
        "path": "/api/v1/search",
        "payload": {
            "query": "Indian heritage",
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {},
        },
        "warmup": 2,
        "iterations": 10,
        "timeout": 30.0,
    },
    "translate": {
        "method": "POST",
        "path": "/api/v1/translate",
        "payload": {
            "text": "नमस्ते, यह एक परीक्षा है।",
            "source_language": "hi",
            "target_language": "en",
        },
        "warmup": 2,
        "iterations": 10,
        "timeout": 10.0,
    },
}


# ============================================================================
# Benchmark Functions
# ============================================================================

async def benchmark_endpoint(
    endpoint_name: str,
    config: dict,
    client: httpx.AsyncClient,
) -> Dict[str, float]:
    """
    Benchmark a single endpoint.

    Args:
        endpoint_name: Name of endpoint
        config: Endpoint configuration
        client: Async HTTP client

    Returns:
        Dictionary with latency statistics
    """
    print(f"\n[Benchmark] {endpoint_name}")

    latencies = []

    # Warmup requests
    for i in range(config["warmup"]):
        try:
            start = time.time()
            if config["method"] == "POST":
                await client.post(
                    config["path"],
                    json=config["payload"],
                    headers=AUTH_HEADERS,
                    timeout=config["timeout"],
                )
            elif config["method"] == "GET":
                await client.get(
                    config["path"],
                    headers=AUTH_HEADERS,
                    timeout=config["timeout"],
                )
            elapsed = (time.time() - start) * 1000
            print(f"  Warmup {i+1}: {elapsed:.0f}ms", end=" ")
        except Exception as e:
            print(f"  Warmup {i+1} failed: {e}")

    print()

    # Actual measurements
    for i in range(config["iterations"]):
        try:
            start = time.time()

            if config["method"] == "POST":
                response = await client.post(
                    config["path"],
                    json=config["payload"],
                    headers=AUTH_HEADERS,
                    timeout=config["timeout"],
                )
            elif config["method"] == "GET":
                response = await client.get(
                    config["path"],
                    headers=AUTH_HEADERS,
                    timeout=config["timeout"],
                )

            elapsed = (time.time() - start) * 1000
            latencies.append(elapsed)

            status = "✓" if response.status_code == 200 else f"✗({response.status_code})"
            print(f"  Iteration {i+1}: {elapsed:.0f}ms {status}")

        except Exception as e:
            print(f"  Iteration {i+1} failed: {e}")

    if not latencies:
        return {}

    # Calculate statistics
    latencies.sort()
    stats = {
        "count": len(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "p50": latencies[int(len(latencies) * 0.50)],
        "p95": latencies[int(len(latencies) * 0.95)],
        "p99": latencies[int(len(latencies) * 0.99)],
    }

    return stats


async def run_benchmarks() -> Dict[str, Dict[str, float]]:
    """
    Run benchmarks for all endpoints.

    Returns:
        Dictionary mapping endpoint names to statistics
    """
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        results = {}

        for endpoint_name, config in ENDPOINTS.items():
            try:
                stats = await benchmark_endpoint(endpoint_name, config, client)
                results[endpoint_name] = stats
            except Exception as e:
                print(f"Failed to benchmark {endpoint_name}: {e}")
                results[endpoint_name] = {"error": str(e)}

        return results


# ============================================================================
# Report Generation
# ============================================================================

def print_report(results: Dict[str, Dict[str, float]]) -> None:
    """
    Print benchmark report.

    Args:
        results: Benchmark results
    """
    print("\n" + "=" * 80)
    print("RESPONSE TIME BENCHMARK REPORT")
    print("=" * 80)

    SLA_P95 = 5000  # 5 seconds in milliseconds

    for endpoint, stats in results.items():
        if "error" in stats:
            print(f"\n{endpoint}: ERROR - {stats['error']}")
            continue

        print(f"\n{endpoint}:")
        print(f"  Iterations: {stats['count']}")
        print(f"  Min:        {stats['min']:.0f}ms")
        print(f"  Mean:       {stats['mean']:.0f}ms")
        print(f"  Median:     {stats['median']:.0f}ms")
        print(f"  Stdev:      {stats['stdev']:.0f}ms")
        print(f"  p50:        {stats['p50']:.0f}ms")
        print(f"  p95:        {stats['p95']:.0f}ms {'✓ SLA OK' if stats['p95'] < SLA_P95 else '✗ SLA VIOLATED'}")
        print(f"  p99:        {stats['p99']:.0f}ms")
        print(f"  Max:        {stats['max']:.0f}ms")

    print("\n" + "=" * 80)
    print("SLA Targets:")
    print(f"  p95 latency: < {SLA_P95}ms")
    print("=" * 80)

    # Summary
    violated = [
        ep for ep, stats in results.items()
        if "error" not in stats and stats.get("p95", 0) >= SLA_P95
    ]

    if violated:
        print(f"\n⚠️  SLA VIOLATIONS ({len(violated)}):")
        for ep in violated:
            print(f"  - {ep}")
    else:
        print("\n✓ All endpoints within SLA")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("Starting response time benchmarks...")
    print(f"Target: {API_BASE_URL}")

    results = asyncio.run(run_benchmarks())
    print_report(results)

    # Save results as JSON
    with open("/tmp/response_time_benchmark.json", "w") as f:
        # Convert to JSON-serializable format
        json_results = {}
        for endpoint, stats in results.items():
            if "error" not in stats:
                json_results[endpoint] = stats

        json.dump(json_results, f, indent=2)
        print(f"\nResults saved to /tmp/response_time_benchmark.json")
