"""
Locust load testing framework for RAG-based Hindi QA system.
Simulates concurrent user load across chat, search, and voice endpoints.

Target SLA: <5s p95 response time
"""

import random
import uuid
from locust import HttpUser, task, between, events
from locust.contrib.statistics import CSVFileWriter
import logging


logger = logging.getLogger(__name__)


# ============================================================================
# Test Data
# ============================================================================

HINDI_QUERIES = [
    "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
    "भारत की विरासत क्या है?",
    "संस्कृति संरक्षण कैसे होता है?",
    "प्राचीन भारतीय कला कहाँ है?",
    "राष्ट्रीय स्मारकों की सूची दें",
]

ENGLISH_QUERIES = [
    "Tell me about Ministry of Culture India",
    "What is Indian heritage?",
    "How is cultural preservation done?",
    "Where is ancient Indian art?",
    "List national monuments",
]

SEARCH_QUERIES = [
    "Indian heritage sites",
    "Ministry of Culture",
    "Cultural preservation",
    "Ancient monuments",
    "Indian art museums",
]


# ============================================================================
# Locust User Classes
# ============================================================================

class ChatUser(HttpUser):
    """User performing chat interactions."""
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session."""
        self.session_id = str(uuid.uuid4())
        self.auth_headers = {
            "Authorization": "Bearer mock-token",
            "Content-Type": "application/json",
        }

    @task(3)
    def chat_hindi(self):
        """Chat with Hindi query."""
        query = random.choice(HINDI_QUERIES)
        payload = {
            "query": query,
            "language": "hi",
            "session_id": self.session_id,
            "chat_history": [],
            "top_k": 10,
            "rerank_top_k": 5,
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def chat_english(self):
        """Chat with English query."""
        query = random.choice(ENGLISH_QUERIES)
        payload = {
            "query": query,
            "language": "en",
            "session_id": self.session_id,
            "chat_history": [],
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def chat_with_history(self):
        """Chat with conversation history."""
        payload = {
            "query": random.choice(HINDI_QUERIES),
            "language": "hi",
            "session_id": self.session_id,
            "chat_history": [
                {"role": "user", "content": "आप कौन हो?"},
                {"role": "assistant", "content": "मैं आपका संस्कृति सहायक हूँ।"},
            ],
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class SearchUser(HttpUser):
    """User performing semantic search."""
    wait_time = between(2, 5)

    def on_start(self):
        """Initialize user session."""
        self.auth_headers = {
            "Authorization": "Bearer mock-token",
            "Content-Type": "application/json",
        }

    @task(2)
    def search_english(self):
        """Search with English query."""
        query = random.choice(SEARCH_QUERIES)
        payload = {
            "query": query,
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {},
        }

        with self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def search_with_filters(self):
        """Search with filters."""
        payload = {
            "query": random.choice(SEARCH_QUERIES),
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {
                "source_sites": ["culture.gov.in"],
                "content_type": "webpage",
            },
        }

        with self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def search_pagination(self):
        """Search with pagination."""
        payload = {
            "query": random.choice(SEARCH_QUERIES),
            "language": "en",
            "page": random.randint(1, 3),
            "page_size": 20,
            "filters": {},
        }

        with self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class VoiceUser(HttpUser):
    """User performing voice interactions."""
    wait_time = between(3, 8)

    def on_start(self):
        """Initialize user session."""
        self.auth_headers = {
            "Authorization": "Bearer mock-token",
        }

    @task(2)
    def translate_hindi_to_english(self):
        """Translate Hindi text to English."""
        text = random.choice(HINDI_QUERIES)
        payload = {
            "text": text,
            "source_language": "hi",
            "target_language": "en",
        }

        with self.client.post(
            "/api/v1/translate",
            json=payload,
            headers={
                **self.auth_headers,
                "Content-Type": "application/json",
            },
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def detect_language(self):
        """Detect language of text."""
        text = random.choice(
            HINDI_QUERIES + ENGLISH_QUERIES
        )
        payload = {
            "text": text,
        }

        with self.client.post(
            "/api/v1/translate/detect",
            json=payload,
            headers={
                **self.auth_headers,
                "Content-Type": "application/json",
            },
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class MixedUser(HttpUser):
    """User performing mixed workload (chat + search + translate)."""
    wait_time = between(1, 4)

    def on_start(self):
        """Initialize user session."""
        self.session_id = str(uuid.uuid4())
        self.auth_headers = {
            "Authorization": "Bearer mock-token",
            "Content-Type": "application/json",
        }

    @task(4)
    def chat(self):
        """Chat query."""
        payload = {
            "query": random.choice(HINDI_QUERIES + ENGLISH_QUERIES),
            "language": random.choice(["hi", "en"]),
            "session_id": self.session_id,
            "chat_history": [],
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def search(self):
        """Search query."""
        payload = {
            "query": random.choice(SEARCH_QUERIES),
            "language": "en",
            "page": 1,
            "page_size": 20,
            "filters": {},
        }

        with self.client.post(
            "/api/v1/search",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def translate(self):
        """Translation query."""
        text = random.choice(HINDI_QUERIES)
        payload = {
            "text": text,
            "source_language": "hi",
            "target_language": "en",
        }

        with self.client.post(
            "/api/v1/translate",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


# ============================================================================
# Locust Events Handlers
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    logger.info("=== Load Test Started ===")
    logger.info(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    logger.info("=== Load Test Completed ===")
    logger.info(f"Total RPS: {environment.stats.total.num_requests}")
    logger.info(f"Avg Response Time: {environment.stats.total.avg_response_time:.0f}ms")
    logger.info(f"p95: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
    logger.info(f"p99: {environment.stats.total.get_response_time_percentile(0.99):.0f}ms")


# ============================================================================
# Locust Configuration
# ============================================================================

"""
Run load tests with:

# Chat-specific load test (100 concurrent users)
locust -f locustfile.py --headless -u 100 -r 10 -t 5m -H http://localhost:8000 ChatUser

# Search-specific load test
locust -f locustfile.py --headless -u 50 -r 5 -t 5m -H http://localhost:8000 SearchUser

# Mixed workload (realistic traffic)
locust -f locustfile.py --headless -u 100 -r 20 -t 10m -H http://localhost:8000 MixedUser

# Web UI for monitoring
locust -f locustfile.py -H http://localhost:8000 ChatUser SearchUser MixedUser
"""
