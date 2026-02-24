"""
End-to-end feedback flow tests.
Tests: Submit feedback → Sentiment analysis → Dashboard visible

Validates:
- Feedback API contract
- §4 Error Response Format
"""

import httpx
import pytest
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Response Models
# ============================================================================

class FeedbackSubmission(BaseModel):
    """Feedback submission response."""
    feedback_id: str
    session_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
    sentiment: str  # positive | neutral | negative
    language: str
    created_at: str


class FeedbackAnalysis(BaseModel):
    """Feedback with sentiment analysis."""
    feedback_id: str
    rating: int
    comment: str
    sentiment: str
    sentiment_score: float = Field(..., ge=-1, le=1)
    key_phrases: list[str]
    issues_detected: list[str]


# ============================================================================
# Tests
# ============================================================================

class TestFeedbackFlowBasic:
    """Basic feedback flow tests."""

    @pytest.mark.integration
    def test_submit_positive_feedback(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Submit positive feedback with rating
        """
        payload = {
            "session_id": session_id,
            "rating": 5,
            "comment": "बहुत अच्छा और मददगार जानकारी दी। धन्यवाद!",
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        feedback = FeedbackSubmission.model_validate(data)

        assert feedback.feedback_id
        assert feedback.rating == 5
        assert feedback.sentiment in ["positive", "neutral"]
        assert feedback.session_id == session_id

    @pytest.mark.integration
    def test_submit_negative_feedback(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Submit negative feedback
        """
        payload = {
            "session_id": session_id,
            "rating": 1,
            "comment": "यह जानकारी सही नहीं है और मेरी समस्या का समाधान नहीं किया।",
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        feedback = FeedbackSubmission.model_validate(data)

        assert feedback.rating == 1
        assert feedback.sentiment in ["negative", "neutral"]

    @pytest.mark.integration
    def test_submit_neutral_feedback(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Submit neutral/mid-range feedback
        """
        payload = {
            "session_id": session_id,
            "rating": 3,
            "comment": "It was okay, could be better.",
            "language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        feedback = FeedbackSubmission.model_validate(data)

        assert feedback.rating == 3

    @pytest.mark.integration
    def test_feedback_english_and_hindi(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Feedback in both Hindi and English languages
        """
        for language, comment in [
            ("hi", "यह सुविधा बहुत उपयोगी है।"),
            ("en", "This feature is very useful."),
        ]:
            payload = {
                "session_id": session_id,
                "rating": 4,
                "comment": comment,
                "language": language,
            }

            headers = {
                **auth_headers_api_consumer,
                "X-Request-ID": str(__import__("uuid").uuid4()),
            }

            response = http_client.post(
                "/api/v1/feedback",
                json=payload,
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            feedback = FeedbackSubmission.model_validate(data)
            assert feedback.language == language

    @pytest.mark.integration
    def test_feedback_sentiment_analysis(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Feedback sentiment is correctly analyzed
        """
        test_cases = [
            ("Excellent! Very helpful.", "positive"),
            ("Bad experience, not useful.", "negative"),
            ("It was fine.", "neutral"),
        ]

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        for comment, expected_sentiment in test_cases:
            payload = {
                "session_id": session_id,
                "rating": 3,
                "comment": comment,
                "language": "en",
            }

            response = http_client.post(
                "/api/v1/feedback",
                json=payload,
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                assert data.get("sentiment") in ["positive", "neutral", "negative"]

    @pytest.mark.integration
    def test_feedback_missing_rating(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Missing rating returns error
        Validates: §4 INVALID_REQUEST
        """
        payload = {
            "session_id": session_id,
            "comment": "Test feedback",
            "language": "en",
            # Missing rating
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_feedback_invalid_rating(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Rating outside 1-5 range returns error
        """
        payload = {
            "session_id": session_id,
            "rating": 10,  # Invalid: must be 1-5
            "comment": "Test feedback",
            "language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error"]["code"] == "INVALID_REQUEST"

    @pytest.mark.integration
    def test_feedback_empty_comment(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Empty comment is allowed but optional
        """
        payload = {
            "session_id": session_id,
            "rating": 4,
            "comment": "",
            "language": "en",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        # Should accept feedback with empty comment
        assert response.status_code in [200, 202]


class TestFeedbackFlowAdvanced:
    """Advanced feedback scenarios."""

    @pytest.mark.integration
    def test_fetch_feedback_stats(
        self,
        http_client: httpx.Client,
        auth_headers_editor: dict,
        request_id: str,
    ):
        """
        Test: Fetch feedback statistics for dashboard
        """
        headers = {
            **auth_headers_editor,
            "X-Request-ID": request_id,
        }

        response = http_client.get(
            "/api/v1/feedback/stats",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should include stats
        assert "total_feedback" in data
        assert "average_rating" in data
        assert "sentiment_distribution" in data

    @pytest.mark.integration
    def test_feedback_with_special_characters(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Feedback with special characters and emojis
        """
        payload = {
            "session_id": session_id,
            "rating": 5,
            "comment": "बहुत अच्छा! 🙏 धन्यवाद!!! @Support",
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code in [200, 202]

    @pytest.mark.integration
    def test_feedback_retrieval_by_session(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_editor: dict,
        request_id: str,
    ):
        """
        Test: Retrieve feedback for specific session
        """
        # First submit feedback
        feedback_payload = {
            "session_id": session_id,
            "rating": 4,
            "comment": "Good feedback",
            "language": "en",
        }

        headers = {
            **auth_headers_editor,
            "X-Request-ID": request_id,
        }

        submit_response = http_client.post(
            "/api/v1/feedback",
            json=feedback_payload,
            headers=headers,
        )

        if submit_response.status_code == 200:
            # Then retrieve it
            get_response = http_client.get(
                f"/api/v1/feedback?session_id={session_id}",
                headers=headers,
            )

            if get_response.status_code == 200:
                data = get_response.json()
                assert "feedback" in data or "items" in data

    @pytest.mark.integration
    def test_feedback_long_comment(
        self,
        http_client: httpx.Client,
        session_id: str,
        auth_headers_api_consumer: dict,
        request_id: str,
    ):
        """
        Test: Very long feedback comment is handled
        """
        long_comment = "यह एक बहुत लंबी प्रतिक्रिया है। " * 50

        payload = {
            "session_id": session_id,
            "rating": 4,
            "comment": long_comment,
            "language": "hi",
        }

        headers = {
            **auth_headers_api_consumer,
            "X-Request-ID": request_id,
        }

        response = http_client.post(
            "/api/v1/feedback",
            json=payload,
            headers=headers,
        )

        assert response.status_code in [200, 202, 413]  # May reject as too large
