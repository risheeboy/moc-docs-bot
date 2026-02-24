"""
Pytest configuration and fixtures for integration testing.
Manages Docker Compose services and provides fixtures for all tests.
"""

import asyncio
import os
import time
import uuid
from typing import AsyncGenerator, Generator
from datetime import datetime

import docker
import httpx
import pytest
import psycopg
import redis
from pymilvus import MilvusClient
from testcontainers.compose import DockerCompose


# ============================================================================
# Global Service Configuration
# ============================================================================

DOCKER_NETWORK = "rag-network"
BASE_URL = "http://localhost"
SERVICES = {
    "api-gateway": 8000,
    "rag-service": 8001,
    "llm-service": 8002,
    "speech-service": 8003,
    "translation-service": 8004,
    "ocr-service": 8005,
    "data-ingestion": 8006,
    "postgres": 5432,
    "redis": 6379,
    "milvus": 19530,
}

EXTERNAL_PORTS = {
    "api-gateway": 8000,
    "rag-service": 8001,
    "llm-service": 8002,
    "speech-service": 8003,
    "translation-service": 8004,
    "ocr-service": 8005,
    "data-ingestion": 8006,
}


# ============================================================================
# Service Health Check
# ============================================================================

async def wait_for_service(
    url: str,
    timeout: float = 120,
    check_interval: float = 2,
    expected_status: int = 200,
) -> bool:
    """
    Wait for a service to become healthy via HTTP GET /health.

    Args:
        url: Service health endpoint URL
        timeout: Maximum seconds to wait
        check_interval: Seconds between checks
        expected_status: Expected HTTP status code

    Returns:
        True if service becomes healthy, False if timeout
    """
    start_time = time.time()

    async with httpx.AsyncClient(timeout=10.0) as client:
        while time.time() - start_time < timeout:
            try:
                response = await client.get(url)
                if response.status_code == expected_status:
                    return True
            except (httpx.ConnectError, httpx.ReadError, asyncio.TimeoutError):
                pass

            await asyncio.sleep(check_interval)

    return False


async def wait_for_all_services(retries: int = 3) -> bool:
    """
    Wait for all backend services to become healthy.

    Args:
        retries: Number of retry attempts

    Returns:
        True if all services healthy, False otherwise
    """
    health_checks = {
        f"{BASE_URL}:{EXTERNAL_PORTS['api-gateway']}/health": "API Gateway",
        f"{BASE_URL}:{EXTERNAL_PORTS['rag-service']}/health": "RAG Service",
        f"{BASE_URL}:{EXTERNAL_PORTS['llm-service']}/health": "LLM Service",
        f"{BASE_URL}:{EXTERNAL_PORTS['speech-service']}/health": "Speech Service",
        f"{BASE_URL}:{EXTERNAL_PORTS['translation-service']}/health": "Translation Service",
        f"{BASE_URL}:{EXTERNAL_PORTS['ocr-service']}/health": "OCR Service",
        f"{BASE_URL}:{EXTERNAL_PORTS['data-ingestion']}/health": "Data Ingestion",
    }

    for attempt in range(retries):
        print(f"\n[Health Check Attempt {attempt + 1}/{retries}]")
        all_healthy = True

        for url, service_name in health_checks.items():
            healthy = await wait_for_service(url, timeout=30)
            status = "✓" if healthy else "✗"
            print(f"  {status} {service_name}")
            if not healthy:
                all_healthy = False

        if all_healthy:
            return True

        print(f"  Waiting {10 * (attempt + 1)}s before retry...")
        await asyncio.sleep(10 * (attempt + 1))

    return False


# ============================================================================
# Pytest Session Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_docker_compose():
    """
    Start Docker Compose services for the entire test session.
    Waits for all services to be healthy.
    """
    print("\n[Setup] Starting Docker Compose services...")

    # Get docker-compose file path (parent directory of testing/)
    docker_compose_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "docker-compose.yml"
    )

    if not os.path.exists(docker_compose_path):
        raise FileNotFoundError(f"docker-compose.yml not found at {docker_compose_path}")

    compose = DockerCompose(
        filepath=docker_compose_path,
        compose_file_name="docker-compose.yml",
        pull=False,
        project_name="rag-qa-test"
    )

    try:
        compose.start()
        print("[Setup] Docker Compose started. Waiting for services...")

        # Wait for all services to be healthy
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if not loop.run_until_complete(wait_for_all_services()):
            raise RuntimeError(
                "Not all services became healthy within timeout. "
                "Check logs with: docker-compose -f docker-compose.yml logs"
            )

        loop.close()
        print("[Setup] All services healthy!")

        yield

    finally:
        print("\n[Teardown] Stopping Docker Compose services...")
        compose.stop()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def http_client() -> Generator[httpx.Client, None, None]:
    """Synchronous HTTP client for making requests to services."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
async def async_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Asynchronous HTTP client for making requests to services."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


# ============================================================================
# Database Connection Fixtures
# ============================================================================

@pytest.fixture
def postgres_conn():
    """PostgreSQL connection for database operations."""
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname=os.getenv("POSTGRES_DB", "ragqa"),
        user=os.getenv("POSTGRES_USER", "ragqa_user"),
        password=os.getenv("POSTGRES_PASSWORD", "test_password"),
    )
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture
def redis_client():
    """Redis client for cache operations."""
    client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )
    # Flush DB before test
    client.flushdb()
    yield client
    # Cleanup after test
    client.flushdb()


@pytest.fixture
def milvus_client():
    """Milvus vector database client."""
    client = MilvusClient(
        uri="http://localhost:19530",
    )
    yield client


@pytest.fixture
def s3_client():
    """AWS S3 client for integration testing."""
    import boto3
    client = boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    )
    yield client


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def session_id() -> str:
    """Generate a unique session ID for test isolation."""
    return str(uuid.uuid4())


@pytest.fixture
def user_id() -> str:
    """Generate a unique user ID for test isolation."""
    return str(uuid.uuid4())


@pytest.fixture
def request_id() -> str:
    """Generate a unique request ID for tracing."""
    return str(uuid.uuid4())


@pytest.fixture
def test_document():
    """Sample document for ingestion tests."""
    return {
        "document_id": str(uuid.uuid4()),
        "title": "Test Document - भारतीय संस्कृति",
        "source_url": "https://culture.gov.in/test",
        "source_site": "culture.gov.in",
        "content": "भारतीय संस्कृति और विरासत के बारे में परीक्षण दस्तावेज़।",
        "content_type": "webpage",
        "language": "hi",
        "metadata": {
            "author": "Test User",
            "published_date": "2026-02-24",
            "tags": ["test", "culture", "heritage"],
        },
    }


@pytest.fixture
def test_query_hindi() -> str:
    """Test query in Hindi."""
    return "भारतीय संस्कृति मंत्रालय के बारे में बताइए"


@pytest.fixture
def test_query_english() -> str:
    """Test query in English."""
    return "Tell me about Ministry of Culture of India"


@pytest.fixture
def test_audio_file() -> bytes:
    """
    Dummy audio file content (WAV header + silent data).
    Real tests would use actual audio files.
    """
    # WAV header for 16-bit mono 16kHz audio
    sample_rate = 16000
    duration_seconds = 1
    num_samples = sample_rate * duration_seconds

    # WAV header
    wav_header = (
        b"RIFF" +
        (36 + num_samples * 2).to_bytes(4, "little") +
        b"WAVE" +
        b"fmt " +
        (16).to_bytes(4, "little") +
        (1).to_bytes(2, "little") +  # PCM
        (1).to_bytes(2, "little") +  # Mono
        sample_rate.to_bytes(4, "little") +
        (sample_rate * 2).to_bytes(4, "little") +
        (2).to_bytes(2, "little") +  # Block align
        (16).to_bytes(2, "little") +  # Bits per sample
        b"data" +
        (num_samples * 2).to_bytes(4, "little")
    )

    # Silent audio data
    audio_data = b"\x00\x00" * num_samples

    return wav_header + audio_data


# ============================================================================
# Auth & Headers Fixtures
# ============================================================================

@pytest.fixture
def auth_headers_admin() -> dict:
    """
    Headers with admin JWT token.
    NOTE: In real tests, obtain token via /auth/login endpoint.
    """
    return {
        "Authorization": "Bearer mock-admin-token",
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_editor() -> dict:
    """Headers with editor JWT token."""
    return {
        "Authorization": "Bearer mock-editor-token",
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_viewer() -> dict:
    """Headers with viewer JWT token."""
    return {
        "Authorization": "Bearer mock-viewer-token",
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_api_consumer() -> dict:
    """Headers with api_consumer JWT token."""
    return {
        "Authorization": "Bearer mock-api-consumer-token",
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data(redis_client, postgres_conn):
    """
    Automatically cleanup test data after each test.
    Clears Redis cache and test records from PostgreSQL.
    """
    yield

    # Clear Redis
    redis_client.flushdb()

    # Delete test records (simplified; real cleanup would be more comprehensive)
    with postgres_conn.cursor() as cur:
        cur.execute("DELETE FROM conversations WHERE session_id LIKE 'test-%'")
        cur.execute("DELETE FROM feedback WHERE created_at > NOW() - INTERVAL '1 minute'")
        cur.execute("COMMIT")


# ============================================================================
# Pytest Hooks
# ============================================================================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Log test outcome and timing information.
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        duration = rep.duration
        status = "PASSED" if rep.passed else "FAILED"
        print(f"\n[Test Result] {item.name}: {status} ({duration:.2f}s)")


# ============================================================================
# Markers Registration
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (takes >5s)"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: mark test as requiring GPU"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
