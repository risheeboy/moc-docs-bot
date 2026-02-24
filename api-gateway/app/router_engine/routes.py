"""Route definitions for semantic router."""

from typing import NamedTuple
from enum import Enum


class RouteType(str, Enum):
    """Types of routes for query classification."""
    FACTUAL = "factual"
    LONG_CONTEXT = "long_context"
    MULTIMODAL = "multimodal"
    TRANSLATION = "translation"
    FALLBACK = "fallback"


class Route(NamedTuple):
    """Route configuration."""
    name: str
    route_type: RouteType
    model: str
    description: str
    examples: list[str]


# Define all routes
ROUTES = {
    RouteType.FACTUAL: Route(
        name="factual",
        route_type=RouteType.FACTUAL,
        model="meta-llama/Llama-3.1-8B-Instruct-AWQ",
        description="Fast, efficient responses to factual questions",
        examples=[
            "भारतीय संस्कृति मंत्रालय के बारे में बताइए",
            "What is the Ministry of Culture?",
            "कौन से विश्व धरोहर स्थल भारत में हैं?",
            "List the national monuments",
        ],
    ),
    RouteType.LONG_CONTEXT: Route(
        name="long_context",
        route_type=RouteType.LONG_CONTEXT,
        model="mistralai/Mistral-NeMo-Instruct-2407-AWQ",
        description="Summarization, long documents, contextual analysis (128K context)",
        examples=[
            "भारत के सांस्कृतिक विरासत नीति की विस्तृत व्याख्या दें",
            "Summarize the entire Ministry culture document",
            "Compare cultural policies across Indian states",
            "Provide comprehensive analysis of ancient Indian art forms",
        ],
    ),
    RouteType.MULTIMODAL: Route(
        name="multimodal",
        route_type=RouteType.MULTIMODAL,
        model="google/gemma-3-12b-it-awq",
        description="Image/video understanding, visual content analysis",
        examples=[
            "इस मूर्ति की व्याख्या करें",
            "What artifacts are shown in these images?",
            "Analyze the architectural style in this photo",
        ],
    ),
    RouteType.TRANSLATION: Route(
        name="translation",
        route_type=RouteType.TRANSLATION,
        model="ai4bharat/indictrans2-indic-en-1B",
        description="Translation between Indian languages",
        examples=[
            "Translate to Hindi",
            "हिंदी को अंग्रेजी में अनुवाद करें",
        ],
    ),
}


def get_route(route_type: RouteType) -> Route:
    """Get route configuration by type."""
    return ROUTES.get(route_type, ROUTES[RouteType.FACTUAL])
