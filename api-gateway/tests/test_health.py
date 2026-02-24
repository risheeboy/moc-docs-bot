"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "api-gateway"
    assert "version" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "dependencies" in data


def test_health_check_headers(client: TestClient):
    """Test health check returns request ID."""
    response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "docs" in data
    assert "redoc" in data
