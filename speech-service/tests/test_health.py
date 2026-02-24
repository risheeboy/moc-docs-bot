"""Tests for Health Check endpoint"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestHealthCheck:
    """Tests for GET /health endpoint"""

    def test_health_check_endpoint_exists(self, client: TestClient):
        """Test that health check endpoint exists and is accessible"""
        response = client.get("/health")

        assert response.status_code in [200, 503]
        assert response.headers.get("Content-Type") == "application/json"

    def test_health_check_response_format(self, client: TestClient):
        """Test health check response format matches specification §5"""
        response = client.get("/health")

        assert response.status_code in [200, 503]
        data = response.json()

        # Verify required fields from §5
        required_fields = [
            "status",
            "service",
            "version",
            "uptime_seconds",
            "timestamp",
            "dependencies",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_health_check_status_field(self, client: TestClient):
        """Test health status field has valid value"""
        response = client.get("/health")

        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_check_service_name(self, client: TestClient):
        """Test service name is correct"""
        response = client.get("/health")

        data = response.json()
        assert data["service"] == "speech-service"

    def test_health_check_version_format(self, client: TestClient):
        """Test version follows semantic versioning"""
        response = client.get("/health")

        data = response.json()
        version = data["version"]

        # Basic SemVer check
        parts = version.split(".")
        assert len(parts) >= 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_health_check_uptime(self, client: TestClient):
        """Test uptime_seconds field is present and positive"""
        response = client.get("/health")

        data = response.json()
        assert data["uptime_seconds"] >= 0
        assert isinstance(data["uptime_seconds"], (int, float))

    def test_health_check_timestamp_format(self, client: TestClient):
        """Test timestamp is in ISO 8601 format"""
        response = client.get("/health")

        data = response.json()
        timestamp_str = data["timestamp"]

        # Try to parse as ISO 8601
        try:
            datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Timestamp not in ISO 8601 format: {timestamp_str}")

    def test_health_check_dependencies_format(self, client: TestClient):
        """Test dependencies field structure"""
        response = client.get("/health")

        data = response.json()
        dependencies = data["dependencies"]

        # Dependencies should be a dict
        assert isinstance(dependencies, dict)

        # Each dependency should have status and latency_ms
        for dep_name, dep_status in dependencies.items():
            assert "status" in dep_status
            assert "latency_ms" in dep_status
            assert dep_status["status"] in [
                "healthy",
                "degraded",
                "unhealthy",
                "unknown",
            ]
            assert isinstance(dep_status["latency_ms"], (int, float))

    def test_health_check_unhealthy_returns_503(self, client: TestClient):
        """Test that unhealthy service returns HTTP 503"""
        response = client.get("/health")

        if response.status_code == 503:
            data = response.json()
            assert data["status"] == "unhealthy"

    def test_health_check_gpu_dependency(self, client: TestClient):
        """Test GPU dependency is checked"""
        response = client.get("/health")

        if response.status_code in [200, 503]:
            data = response.json()
            dependencies = data["dependencies"]

            # GPU dependency should be present
            assert "gpu" in dependencies

    def test_health_check_models_dependency(self, client: TestClient):
        """Test models dependency is checked"""
        response = client.get("/health")

        if response.status_code in [200, 503]:
            data = response.json()
            dependencies = data["dependencies"]

            # Models dependency should be present
            assert "models" in dependencies

    def test_health_check_consistent_status(self, client: TestClient):
        """Test health status is consistent across multiple calls"""
        response1 = client.get("/health")
        response2 = client.get("/health")

        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()

            # Status should remain the same within a short timeframe
            assert data1["status"] == data2["status"]
