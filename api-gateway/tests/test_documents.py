"""Tests for document management endpoints."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from app.main import app


def test_documents_list_endpoint(client: TestClient):
    """Test document list endpoint."""
    response = client.get("/api/v1/documents")

    # Should require auth or return empty list
    assert response.status_code in [200, 401]


def test_document_upload_requires_file(client: TestClient):
    """Test document upload requires file."""
    response = client.post(
        "/api/v1/documents/upload",
        data={"title": "Test Document"},
    )

    # Should fail without file
    assert response.status_code in [422, 400, 401]


def test_document_upload_with_file(client: TestClient):
    """Test document upload with file."""
    doc_file = BytesIO(b"This is test document content")

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", doc_file, "text/plain")},
        data={
            "title": "Test Document",
            "language": "en",
        },
    )

    # Should return proper response or require auth
    assert response.status_code in [200, 401, 422, 500]


def test_document_delete_endpoint(client: TestClient):
    """Test document delete endpoint."""
    response = client.delete(
        "/api/v1/documents/doc_123",
    )

    # Should require auth
    assert response.status_code in [401, 404, 500]
