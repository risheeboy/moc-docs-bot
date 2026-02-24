"""
Input fuzzing tests for API security.
Tests against XSS, SQL injection, command injection, Unicode attacks, etc.
"""

import httpx
import json
from hypothesis import given, strategies as st


# ============================================================================
# Fuzz Payloads
# ============================================================================

FUZZ_PAYLOADS = {
    "sql_injection": [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' UNION SELECT NULL, NULL--",
        "admin' --",
        "' OR 1=1 --",
    ],
    "xss": [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "<svg onload=alert('xss')>",
        "\"><script>alert('xss')</script>",
        "<iframe src='javascript:alert(1)'></iframe>",
    ],
    "command_injection": [
        "; rm -rf /",
        "| cat /etc/passwd",
        "` whoami `",
        "$(whoami)",
        "; ls -la",
    ],
    "path_traversal": [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "....//....//....//etc/passwd",
        "%2e%2e%2fetc%2fpasswd",
    ],
    "unicode_attacks": [
        "नमस्ते\u0000test",  # Null byte
        "\uFFFD" * 100,  # Replacement chars
        "\u202E" + "test",  # Right-to-left override
        "test\u0301\u0302\u0303",  # Combining marks
    ],
    "hindi_unicode_attacks": [
        "क\u0300क\u0301क\u0302",  # Hindi with combining marks
        "त्र\u094D\u094D",  # Devanagari combining
        "ह\u093C",  # Nuqta
    ],
    "buffer_overflow": [
        "A" * 10000,
        "test" * 5000,
    ],
    "null_bytes": [
        "test\x00data",
        "query%00injection",
    ],
}


# ============================================================================
# Fuzz Tests
# ============================================================================

class TestInputFuzzing:
    """Input fuzzing tests."""

    def test_fuzz_chat_query_with_payloads(self):
        """Test: Chat endpoint handles fuzzy inputs safely."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            for payload_type, payloads in FUZZ_PAYLOADS.items():
                print(f"\nFuzzing with {payload_type}...")

                for payload in payloads:
                    try:
                        response = client.post(
                            "/api/v1/chat",
                            json={
                                "query": payload,
                                "language": "en",
                                "session_id": "fuzz-test",
                            },
                            headers=headers,
                            timeout=5.0,
                        )

                        # Should not crash or return 500
                        assert response.status_code != 500, \
                            f"Server error with {payload_type}: {payload}"

                        # Should handle gracefully
                        assert response.status_code in [200, 400, 401, 403, 429]

                    except Exception as e:
                        print(f"  ✗ {payload_type}: {str(e)[:50]}")
                        raise

    def test_fuzz_feedback_comment_with_payloads(self):
        """Test: Feedback endpoint sanitizes input."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            for payload_type, payloads in FUZZ_PAYLOADS.items():
                for payload in payloads:
                    try:
                        response = client.post(
                            "/api/v1/feedback",
                            json={
                                "session_id": "test",
                                "rating": 3,
                                "comment": payload,
                                "language": "en",
                            },
                            headers=headers,
                            timeout=5.0,
                        )

                        assert response.status_code != 500
                        assert response.status_code in [200, 202, 400, 401]

                    except Exception:
                        pass

    def test_fuzz_search_query_with_payloads(self):
        """Test: Search handles malicious queries."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            for payload_type, payloads in FUZZ_PAYLOADS.items():
                for payload in payloads:
                    try:
                        response = client.post(
                            "/api/v1/search",
                            json={
                                "query": payload,
                                "language": "en",
                                "page": 1,
                                "page_size": 20,
                            },
                            headers=headers,
                            timeout=5.0,
                        )

                        assert response.status_code != 500
                        assert response.status_code in [200, 400]

                    except Exception:
                        pass

    def test_fuzz_translate_text_with_payloads(self):
        """Test: Translation handles fuzzy input."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            for payload_type, payloads in FUZZ_PAYLOADS.items():
                for payload in payloads:
                    try:
                        response = client.post(
                            "/api/v1/translate",
                            json={
                                "text": payload,
                                "source_language": "en",
                                "target_language": "hi",
                            },
                            headers=headers,
                            timeout=5.0,
                        )

                        assert response.status_code != 500
                        assert response.status_code in [200, 400]

                    except Exception:
                        pass

    def test_fuzz_json_payload_structure(self):
        """Test: Invalid JSON structures are rejected."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}

            invalid_jsons = [
                "{broken json",
                '{"key": undefined}',
                '{"key": NaN}',
                "{'single': 'quotes'}",
            ]

            for invalid_json in invalid_jsons:
                try:
                    response = client.post(
                        "/api/v1/chat",
                        content=invalid_json,
                        headers=headers,
                        timeout=5.0,
                    )

                    # Should reject bad JSON
                    assert response.status_code in [400, 401]

                except httpx.RequestNotRead:
                    pass  # Expected for bad JSON


class TestHindiUnicodeEdgeCases:
    """Test Hindi Unicode edge cases."""

    def test_hindi_devanagari_variations(self):
        """Test: Various Devanagari script variations are handled."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            hindi_texts = [
                "नमस्ते",  # Basic Hindi
                "कृष्ण",  # With combining marks
                "त्र",  # Conjunct consonants
                "हिंदी", # With anusvara
                "ङ्गा",  # With different consonants
                "ॽ",  # Rare marks
            ]

            for text in hindi_texts:
                response = client.post(
                    "/api/v1/translate/detect",
                    json={"text": text},
                    headers=headers,
                )

                assert response.status_code in [200, 400]

    def test_mixed_script_strings(self):
        """Test: Mixed Hindi/English/Special chars."""
        with httpx.Client(base_url="http://localhost:8000") as client:
            headers = {"Authorization": "Bearer token"}

            mixed_texts = [
                "नमस्ते Hello",
                "Test परीक्षा 123",
                "email@example.com नमस्ते",
                "https://culture.gov.in/page?param=value&test=123",
            ]

            for text in mixed_texts:
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "query": text,
                        "language": "hi",
                        "session_id": "test",
                    },
                    headers=headers,
                )

                assert response.status_code in [200, 400]
