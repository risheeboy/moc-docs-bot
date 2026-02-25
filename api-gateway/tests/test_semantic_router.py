"""Tests for semantic router."""

import pytest
from app.router_engine.semantic_router import SemanticRouter
from app.router_engine.routes import RouteType


def test_factual_query_routing():
    """Test factual queries route to standard model."""
    router = SemanticRouter()

    route = router.route("What is the Ministry of Culture?", "en")
    assert route.route_type == RouteType.FACTUAL
    assert "llama" in route.model.lower() or "instruct" in route.model.lower()


def test_long_context_query_routing():
    """Test long queries route to long-context model."""
    router = SemanticRouter()

    # Query with >200 characters triggers long-context
    long_query = (
        "Provide a comprehensive analysis of Indian cultural heritage "
        "including historical evolution, contemporary significance, "
        "and future preservation strategies across all states and regions "
        "with detailed explanations of each aspect and how they connect"
    )

    route = router.route(long_query, "en")
    assert route.route_type == RouteType.LONG_CONTEXT
    assert "mistral" in route.model.lower() or "nemo" in route.model.lower()


def test_translation_query_routing():
    """Test translation requests route to translation model."""
    router = SemanticRouter()

    route = router.route("Translate this to Hindi", "en")
    assert route.route_type == RouteType.TRANSLATION


def test_hindi_query_routing():
    """Test Hindi language queries."""
    router = SemanticRouter()

    route = router.route("भारतीय संस्कृति के बारे में बताइए", "hi")
    assert route.route_type == RouteType.FACTUAL


def test_chat_history_influences_routing():
    """Test that chat history influences route selection."""
    router = SemanticRouter()

    chat_history = [
        {"role": "user", "content": "Tell me about Indian monuments"},
        {"role": "assistant", "content": "Indian monuments are..."},
        {"role": "user", "content": "Give me more details"},
    ]

    route = router.route("And what about their history?", "en", chat_history)
    # With history, should prefer long-context for follow-up questions
    assert route is not None


def test_all_routes_available():
    """Test all routes can be retrieved."""
    router = SemanticRouter()

    routes = router.get_all_routes()
    assert len(routes) > 0
    assert RouteType.FACTUAL in routes
    assert RouteType.LONG_CONTEXT in routes
    assert RouteType.MULTIMODAL in routes
    assert RouteType.TRANSLATION in routes
