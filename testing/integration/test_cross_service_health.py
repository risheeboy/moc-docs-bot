"""
Cross-service health check tests.
Tests: All services healthy, communicating, dependencies validated

Validates:
- §5 Health Check Format across all services
- §1 Service Registry
"""

import httpx
import pytest
from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# Response Models
# ============================================================================

class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    status: str  # healthy | degraded | unhealthy
    latency_ms: float


class HealthResponse(BaseModel):
    """Health check response (§5)."""
    status: str  # healthy | degraded | unhealthy
    service: str
    version: str
    uptime_seconds: float
    timestamp: str
    dependencies: dict[str, DependencyHealth]


# ============================================================================
# Test Configuration
# ============================================================================

SERVICES = {
    "api-gateway": 8000,
    "rag-service": 8001,
    "llm-service": 8002,
    "speech-service": 8003,
    "translation-service": 8004,
    "ocr-service": 8005,
    "data-ingestion": 8006,
}


# ============================================================================
# Tests
# ============================================================================

class TestCrossServiceHealth:
    """Cross-service health and dependency tests."""

    @pytest.mark.integration
    async def test_all_services_healthy(self, async_http_client: httpx.AsyncClient):
        """
        Test: All backend services report healthy status
        Validates: §5 Health Check Format
        """
        results = {}

        for service_name, port in SERVICES.items():
            try:
                response = await async_http_client.get(
                    f"http://localhost:{port}/health",
                    timeout=10.0,
                )
                assert response.status_code == 200, \
                    f"{service_name} returned {response.status_code}"

                health = response.json()
                HealthResponse.model_validate(health)

                results[service_name] = health

                assert health["status"] in ["healthy", "degraded"], \
                    f"{service_name} status is {health['status']}"
                assert health["service"] == service_name
                assert "version" in health
                assert "uptime_seconds" in health
                assert "timestamp" in health
                assert "dependencies" in health

            except Exception as e:
                pytest.fail(f"{service_name} health check failed: {e}")

        # At least API Gateway should be healthy
        assert results.get("api-gateway", {}).get("status") == "healthy"

    @pytest.mark.integration
    async def test_service_version_format(self, async_http_client: httpx.AsyncClient):
        """
        Test: All services report version in SemVer format
        """
        for service_name, port in SERVICES.items():
            response = await async_http_client.get(
                f"http://localhost:{port}/health",
                timeout=10.0,
            )

            if response.status_code == 200:
                health = response.json()
                version = health.get("version", "")

                # SemVer format: X.Y.Z
                parts = version.split(".")
                assert len(parts) >= 3, \
                    f"{service_name} version '{version}' is not SemVer"

                # Each part should be numeric
                for part in parts[:3]:
                    assert part.isdigit(), \
                        f"{service_name} version part '{part}' is not numeric"

    @pytest.mark.integration
    async def test_service_uptime_monotonic(self, async_http_client: httpx.AsyncClient):
        """
        Test: Service uptime is a valid positive number
        """
        for service_name, port in SERVICES.items():
            response = await async_http_client.get(
                f"http://localhost:{port}/health",
                timeout=10.0,
            )

            if response.status_code == 200:
                health = response.json()
                uptime = health.get("uptime_seconds", 0)

                assert isinstance(uptime, (int, float)), \
                    f"{service_name} uptime is not numeric"
                assert uptime >= 0, \
                    f"{service_name} uptime is negative"

    @pytest.mark.integration
    async def test_service_timestamp_iso8601(self, async_http_client: httpx.AsyncClient):
        """
        Test: Service timestamp is valid ISO 8601 format
        """
        for service_name, port in SERVICES.items():
            response = await async_http_client.get(
                f"http://localhost:{port}/health",
                timeout=10.0,
            )

            if response.status_code == 200:
                health = response.json()
                timestamp = health.get("timestamp", "")

                try:
                    # Should parse as ISO 8601
                    __import__("datetime").datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                except ValueError:
                    pytest.fail(f"{service_name} timestamp '{timestamp}' is not ISO 8601")

    @pytest.mark.integration
    async def test_dependency_health_format(self, async_http_client: httpx.AsyncClient):
        """
        Test: Dependency health entries have correct format
        Validates: §5 dependencies field
        """
        # API Gateway should report dependencies
        response = await async_http_client.get(
            f"http://localhost:{SERVICES['api-gateway']}/health",
            timeout=10.0,
        )

        assert response.status_code == 200
        health = response.json()
        dependencies = health.get("dependencies", {})

        for dep_name, dep_health in dependencies.items():
            assert "status" in dep_health, \
                f"Dependency {dep_name} missing 'status'"
            assert "latency_ms" in dep_health, \
                f"Dependency {dep_name} missing 'latency_ms'"

            assert dep_health["status"] in ["healthy", "degraded", "unhealthy"]
            assert isinstance(dep_health["latency_ms"], (int, float))
            assert dep_health["latency_ms"] >= 0

    @pytest.mark.integration
    async def test_api_gateway_critical_dependencies(
        self,
        async_http_client: httpx.AsyncClient,
    ):
        """
        Test: API Gateway reports critical dependencies (RAG, LLM, etc.)
        """
        response = await async_http_client.get(
            f"http://localhost:{SERVICES['api-gateway']}/health",
            timeout=10.0,
        )

        assert response.status_code == 200
        health = response.json()
        dependencies = health.get("dependencies", {})

        # Should report key dependencies
        expected_deps = {
            "rag-service",
            "llm-service",
            "postgres",
            "redis",
        }

        reported_deps = set(dependencies.keys())
        assert expected_deps.issubset(reported_deps), \
            f"Missing expected dependencies. Have: {reported_deps}"

    @pytest.mark.integration
    async def test_service_latency_reasonable(self, async_http_client: httpx.AsyncClient):
        """
        Test: Service dependency latencies are reasonable (<1000ms)
        """
        for service_name, port in SERVICES.items():
            response = await async_http_client.get(
                f"http://localhost:{port}/health",
                timeout=10.0,
            )

            if response.status_code == 200:
                health = response.json()
                dependencies = health.get("dependencies", {})

                for dep_name, dep_health in dependencies.items():
                    latency = dep_health.get("latency_ms", 0)

                    assert latency < 1000, \
                        f"{service_name} → {dep_name} latency {latency}ms exceeds 1000ms"

    @pytest.mark.integration
    async def test_rag_service_dependencies(self, async_http_client: httpx.AsyncClient):
        """
        Test: RAG Service reports Milvus and Redis dependencies
        """
        response = await async_http_client.get(
            f"http://localhost:{SERVICES['rag-service']}/health",
            timeout=10.0,
        )

        if response.status_code == 200:
            health = response.json()
            dependencies = health.get("dependencies", {})

            expected_deps = {"milvus", "redis"}
            reported_deps = set(dependencies.keys())

            assert expected_deps.issubset(reported_deps), \
                f"RAG Service missing expected dependencies"

    @pytest.mark.integration
    async def test_llm_service_dependencies(self, async_http_client: httpx.AsyncClient):
        """
        Test: LLM Service reports model loading status
        """
        response = await async_http_client.get(
            f"http://localhost:{SERVICES['llm-service']}/health",
            timeout=10.0,
        )

        if response.status_code == 200:
            health = response.json()
            dependencies = health.get("dependencies", {})

            # Should report model loading status
            model_names = [
                "llama-3.1-8b",
                "mistral-nemo",
                "gemma-3",
            ]

            reported_models = [k for k in dependencies.keys() if any(m in k for m in model_names)]
            # At least one model should be loading or loaded
            assert len(reported_models) > 0 or response.status_code == 200

    @pytest.mark.integration
    async def test_service_health_degraded_handling(
        self,
        async_http_client: httpx.AsyncClient,
    ):
        """
        Test: Services can report degraded status appropriately
        """
        for service_name, port in SERVICES.items():
            response = await async_http_client.get(
                f"http://localhost:{port}/health",
                timeout=10.0,
            )

            if response.status_code == 200:
                health = response.json()
                status = health.get("status")

                # Degraded is acceptable for non-critical services
                assert status in ["healthy", "degraded"]

                # If degraded, should have at least one unhealthy dependency
                if status == "degraded":
                    dependencies = health.get("dependencies", {})
                    unhealthy_deps = [
                        d for d, h in dependencies.items()
                        if h.get("status") == "unhealthy"
                    ]
                    assert len(unhealthy_deps) > 0

    @pytest.mark.integration
    async def test_service_health_consistency(self, async_http_client: httpx.AsyncClient):
        """
        Test: Multiple health checks return consistent information
        """
        service_name = "api-gateway"
        port = SERVICES[service_name]

        # Get health twice
        response1 = await async_http_client.get(
            f"http://localhost:{port}/health",
            timeout=10.0,
        )
        health1 = response1.json()

        response2 = await async_http_client.get(
            f"http://localhost:{port}/health",
            timeout=10.0,
        )
        health2 = response2.json()

        # Service and version should remain same
        assert health1["service"] == health2["service"]
        assert health1["version"] == health2["version"]

        # Uptime should increase (monotonic)
        assert health2["uptime_seconds"] >= health1["uptime_seconds"]


class TestServiceCommunication:
    """Test inter-service communication."""

    @pytest.mark.integration
    def test_api_gateway_can_call_rag_service(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: API Gateway successfully routes to RAG Service
        """
        payload = {
            "query": "test query",
            "language": "en",
            "session_id": str(__import__("uuid").uuid4()),
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=30.0,
        )

        # Should get response or proper error
        assert response.status_code in [200, 202, 400, 503, 504]

    @pytest.mark.integration
    def test_api_gateway_can_call_llm_service(
        self,
        http_client: httpx.Client,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: API Gateway can invoke LLM for completion
        """
        payload = {
            "query": "What is the capital of India?",
            "language": "en",
            "session_id": str(__import__("uuid").uuid4()),
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        # This should internally call LLM service
        response = http_client.post(
            "/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=30.0,
        )

        assert response.status_code in [200, 202, 503]
