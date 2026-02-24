"""Language detection middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging

logger = logging.getLogger(__name__)


class LanguageDetectorMiddleware(BaseHTTPMiddleware):
    """Detect query language and handle code-mixed Hindi-English."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Detect language in request and store in state."""
        try:
            # Only detect for chat and search endpoints
            if request.method == "POST" and "/chat" in request.url.path:
                body = await request.body()
                if body:
                    import json

                    try:
                        data = json.loads(body)
                        if "query" in data:
                            detected_lang = self._detect_language(data["query"])
                            request.state.detected_language = detected_lang
                    except json.JSONDecodeError:
                        pass

                # Restore body for actual handler
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive

            elif request.method == "GET" and "/search" in request.url.path:
                query = request.query_params.get("query")
                if query:
                    detected_lang = self._detect_language(query)
                    request.state.detected_language = detected_lang
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            request.state.detected_language = None

        response = await call_next(request)
        return response

    @staticmethod
    def _detect_language(text: str) -> str:
        """
        Detect language from text.

        Handles code-mixed Hindi-English by returning most probable language.
        """
        if not text or len(text.strip()) < 2:
            return "en"

        try:
            # Get probabilities for all detected languages
            probs = detect_langs(text)
            if probs:
                # Return the most probable language
                lang = probs[0].lang
                # Map to our supported codes
                lang_map = {
                    "hi": "hi",
                    "en": "en",
                    "bn": "bn",
                    "te": "te",
                    "mr": "mr",
                    "ta": "ta",
                    "ur": "ur",
                    "gu": "gu",
                    "kn": "kn",
                    "ml": "ml",
                    "or": "or",
                    "pa": "pa",
                }
                return lang_map.get(lang, "en")
        except LangDetectException:
            pass

        return "en"
