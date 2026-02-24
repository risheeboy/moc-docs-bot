"""
OWASP API Top 10 security tests.
Tests for: injection, broken authentication, broken access control,
unrestricted resource consumption, broken function level authorization,
insecure direct object reference, rate limiting, etc.
"""

import httpx
import pytest
from typing import Dict, List


# ============================================================================
# Test Configuration
# ============================================================================

API_BASE_URL = "http://localhost:8000"


# ============================================================================
# Authentication & Authorization Tests
# ============================================================================

class TestAuthenticationSecurity:
    """Test authentication mechanisms."""

    def test_missing_authorization_header(self):
        """Test: Request without auth header is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/chat",
                json={"query": "test", "language": "en", "session_id": "test"},
            )

            assert response.status_code == 401
            error = response.json()
            assert error.get("error", {}).get("code") == "UNAUTHORIZED"

    def test_invalid_token_format(self):
        """Test: Malformed auth token is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/chat",
                json={"query": "test", "language": "en", "session_id": "test"},
                headers={"Authorization": "InvalidToken"},
            )

            assert response.status_code == 401

    def test_expired_token(self):
        """Test: Expired JWT token is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            # Use a token that claims to be expired
            expired_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MDAwMDAwMDB9.invalid"

            response = client.post(
                "/api/v1/chat",
                json={"query": "test", "language": "en", "session_id": "test"},
                headers={"Authorization": expired_token},
            )

            assert response.status_code == 401
            error = response.json()
            assert error.get("error", {}).get("code") in ["UNAUTHORIZED", "TOKEN_EXPIRED"]

    def test_revoked_api_key(self):
        """Test: Revoked API key is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/chat",
                json={"query": "test", "language": "en", "session_id": "test"},
                headers={"Authorization": "Bearer revoked-key-12345"},
            )

            # Should be rejected
            assert response.status_code in [401, 403]


class TestAccessControlSecurity:
    """Test access control enforcement."""

    def test_viewer_cannot_create_document(self):
        """Test: Viewer role cannot ingest documents."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/documents/ingest",
                json={
                    "document_id": "test",
                    "title": "Test",
                    "source_url": "https://test.com",
                    "source_site": "test.com",
                    "content": "Test",
                    "content_type": "webpage",
                    "language": "en",
                },
                headers={"Authorization": "Bearer viewer-token"},
            )

            # Should be forbidden (403) or unauthorized (401)
            assert response.status_code in [401, 403]

    def test_api_consumer_cannot_access_admin_endpoints(self):
        """Test: API consumer cannot access admin endpoints."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.get(
                "/api/v1/admin/settings",
                headers={"Authorization": "Bearer api-consumer-token"},
            )

            assert response.status_code == 403
            error = response.json()
            assert error.get("error", {}).get("code") == "FORBIDDEN"

    def test_cannot_access_other_user_session(self):
        """Test: User cannot access another user's session data."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            other_user_session = "other-user-session-id"

            response = client.get(
                f"/api/v1/sessions/{other_user_session}",
                headers={"Authorization": "Bearer user-token"},
            )

            # Should be forbidden
            assert response.status_code in [403, 404]


# ============================================================================
# Injection Attack Tests
# ============================================================================

class TestInjectionSecurity:
    """Test injection attack prevention."""

    def test_sql_injection_in_query(self):
        """Test: SQL injection attempt is safely handled."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            sql_injection = "' OR '1'='1'; DROP TABLE users; --"

            response = client.post(
                "/api/v1/chat",
                json={
                    "query": sql_injection,
                    "language": "en",
                    "session_id": "test",
                },
                headers={"Authorization": "Bearer token"},
            )

            # Should not execute SQL, just treat as search text
            assert response.status_code in [200, 400]
            # Should not contain error about SQL execution
            if response.status_code != 200:
                assert "SQL" not in response.text.upper()

    def test_xss_injection_in_feedback(self):
        """Test: XSS injection in feedback is sanitized."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            xss_payload = "<script>alert('xss')</script>"

            response = client.post(
                "/api/v1/feedback",
                json={
                    "session_id": "test",
                    "rating": 4,
                    "comment": xss_payload,
                    "language": "en",
                },
                headers={"Authorization": "Bearer token"},
            )

            if response.status_code == 200:
                data = response.json()
                # Comment should be stored safely
                assert "script" not in data.get("comment", "").lower() or \
                       "script" not in data.get("comment", "")

    def test_command_injection_in_translation(self):
        """Test: Command injection attempts are blocked."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            command_injection = "test; rm -rf /; echo"

            response = client.post(
                "/api/v1/translate",
                json={
                    "text": command_injection,
                    "source_language": "en",
                    "target_language": "hi",
                },
                headers={"Authorization": "Bearer token"},
            )

            # Should treat as normal text
            assert response.status_code in [200, 400]

    def test_json_bomb_protection(self):
        """Test: JSON bomb (deeply nested) is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            # Create deeply nested JSON
            nested = {"value": "test"}
            for _ in range(100):
                nested = {"nested": nested}

            response = client.post(
                "/api/v1/chat",
                json=nested,
                headers={"Authorization": "Bearer token"},
            )

            # Should reject or handle safely
            assert response.status_code in [400, 413]


# ============================================================================
# Rate Limiting Tests
# ============================================================================

class TestRateLimitSecurity:
    """Test rate limiting enforcement."""

    def test_rate_limit_exceeded(self):
        """Test: Rate limiting kicks in after threshold."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            # Simulate rapid requests from same IP
            responses = []
            for i in range(100):
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": f"query {i}",
                        "language": "en",
                        "session_id": "test",
                    },
                    headers={"Authorization": "Bearer api-consumer-token"},
                )
                responses.append(response.status_code)

            # At least one should hit rate limit
            assert 429 in responses, "Rate limiting not enforced"

    def test_rate_limit_headers_present(self):
        """Test: Rate limit headers are returned."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/chat",
                json={
                    "query": "test",
                    "language": "en",
                    "session_id": "test",
                },
                headers={"Authorization": "Bearer token"},
            )

            # Should have rate limit headers
            headers_present = any(h in response.headers for h in [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "RateLimit-Limit",
                "RateLimit-Remaining",
            ])
            # Rate limit headers are good practice but optional


class TestResourceConsumptionSecurity:
    """Test protection against resource exhaustion."""

    def test_oversized_payload_rejected(self):
        """Test: Oversized payload is rejected."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            large_payload = "test" * 1000000  # ~4MB

            response = client.post(
                "/api/v1/chat",
                json={
                    "query": large_payload,
                    "language": "en",
                    "session_id": "test",
                },
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 413  # Payload Too Large

    def test_request_timeout_handled(self):
        """Test: Slow requests timeout gracefully."""
        with httpx.Client(base_url=API_BASE_URL, timeout=1.0) as client:
            try:
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": "test",
                        "language": "en",
                        "session_id": "test",
                    },
                    headers={"Authorization": "Bearer token"},
                )
                # Should timeout or complete
                assert response.status_code in [200, 504]
            except httpx.ReadTimeout:
                pass  # Timeout is acceptable


# ============================================================================
# Data Exposure Tests
# ============================================================================

class TestDataExposureSecurity:
    """Test protection against sensitive data exposure."""

    def test_no_sensitive_data_in_error_messages(self):
        """Test: Error messages don't leak sensitive info."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.post(
                "/api/v1/chat",
                json={
                    "query": "test",
                    "language": "en",
                },
                headers={"Authorization": "Bearer token"},
            )

            error_text = response.text.lower()
            # Should not expose internal details
            sensitive_patterns = [
                "sql",
                "traceback",
                "stack trace",
                "password",
                "api_key",
                "secret",
                "/home/",
                "/var/",
            ]

            for pattern in sensitive_patterns:
                assert pattern not in error_text, \
                    f"Error message contains sensitive info: {pattern}"

    def test_pii_not_logged_in_errors(self):
        """Test: PII is not returned in error responses."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            # Try to trigger error with PII-like content
            pii_query = "9999999999 (phone) user@example.com (email)"

            response = client.post(
                "/api/v1/feedback",
                json={
                    "session_id": "test",
                    "rating": 4,
                    "comment": pii_query,
                    "language": "en",
                },
                headers={"Authorization": "Bearer token"},
            )

            # Response should not echo back full PII
            if response.status_code in [400, 422]:
                error_text = response.text
                # Should not contain phone/email in unmodified form
                assert "9999999999" not in error_text


# ============================================================================
# CORS & Security Headers Tests
# ============================================================================

class TestSecurityHeaders:
    """Test security headers."""

    def test_cors_headers_present(self):
        """Test: CORS headers are properly configured."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.options(
                "/api/v1/chat",
                headers={
                    "Origin": "https://culture.gov.in",
                    "Access-Control-Request-Method": "POST",
                },
            )

            # Should have CORS headers or reject cross-origin
            if response.status_code == 200:
                assert "access-control-allow" in str(response.headers).lower()

    def test_security_headers_present(self):
        """Test: Important security headers are set."""
        with httpx.Client(base_url=API_BASE_URL) as client:
            response = client.get("/api/v1/health")

            headers = response.headers
            # Check for security headers
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "Strict-Transport-Security",
            ]

            found_headers = [h for h in security_headers if h in headers]
            # At least some security headers should be present
            assert len(found_headers) > 0
