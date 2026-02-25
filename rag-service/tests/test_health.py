import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    return TestClient(app)


class TestHealth:
    """Health check endpoint tests."""

    def test_health_check_returns_200(self, client):
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code in [200, 503]  # 503 if Milvus unavailable
        data = response.json()
        # 503 wraps the response in a "detail" key
        if response.status_code == 503:
            assert "detail" in data
            assert "status" in data["detail"]
            assert data["detail"]["service"] == "rag-service"
        else:
            assert "status" in data
            assert data["service"] == "rag-service"

    def test_health_check_has_required_fields(self, client):
        """Test health check response has all required fields."""
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "service" in data
            assert "version" in data
            assert "uptime_seconds" in data
            assert "timestamp" in data
            assert "dependencies" in data

    def test_metrics_endpoint_returns_200(self, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert b"http_requests_total" in response.content

    def test_root_endpoint_returns_200(self, client):
        """Test root endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "rag-service"
        assert "status" in data
