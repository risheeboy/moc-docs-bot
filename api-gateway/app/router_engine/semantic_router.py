"""Semantic router - classifies queries and routes to appropriate LLM model."""

import logging
from typing import Optional
from .routes import Route, RouteType, get_route, ROUTES
from .embeddings import RouterEmbeddings

logger = logging.getLogger(__name__)


class SemanticRouter:
    """Route queries to appropriate LLM model based on query characteristics."""

    def __init__(self, embeddings: Optional[RouterEmbeddings] = None):
        """Initialize semantic router."""
        self.embeddings = embeddings or RouterEmbeddings()

    def route(
        self, query: str, language: str = "en", chat_history: Optional[list] = None
    ) -> Route:
        """
        Route query to appropriate LLM model.

        Returns:
            Route object containing model name and metadata
        """
        route_type = self._classify_query(query, language, chat_history)
        return get_route(route_type)

    def _classify_query(
        self, query: str, language: str = "en", chat_history: Optional[list] = None
    ) -> RouteType:
        """Classify query to determine best route."""
        # Keywords that indicate different route types
        long_context_keywords = [
            "summarize",
            "comprehensive",
            "explain",
            "detailed",
            "analysis",
            "compare",
            "overview",
            "history",
            "evolution",
            "सारांश",
            "विस्तृत",
            "विश्लेषण",
            "तुलना",
        ]

        translation_keywords = [
            "translate",
            "translation",
            "convert",
            "अनुवाद",
            "अनुवाद करें",
            "हिंदी",
            "अंग्रेजी",
        ]

        multimodal_keywords = [
            "image",
            "photo",
            "picture",
            "visual",
            "video",
            "see",
            "show",
            "look",
            "चित्र",
            "फोटो",
            "देखें",
            "दिखाएं",
        ]

        query_lower = query.lower()

        # Check for translation requests
        if any(keyword in query_lower for keyword in translation_keywords):
            return RouteType.TRANSLATION

        # Check for multimodal content
        if any(keyword in query_lower for keyword in multimodal_keywords):
            return RouteType.MULTIMODAL

        # Check for long-context queries
        # Long queries (>200 chars) or history-based queries
        if len(query) > 200 or any(
            keyword in query_lower for keyword in long_context_keywords
        ):
            # Check if conversation history exists (multi-turn)
            if chat_history and len(chat_history) > 2:
                return RouteType.LONG_CONTEXT

        # Check word count as additional signal
        word_count = len(query.split())
        if word_count > 30:
            return RouteType.LONG_CONTEXT

        # Default to factual (fast) route
        return RouteType.FACTUAL

    def get_all_routes(self) -> dict[str, Route]:
        """Get all available routes."""
        return ROUTES
