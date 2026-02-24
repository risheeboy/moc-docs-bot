import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class RerankerService:
    """
    Cross-encoder reranking for improved retrieval results.

    Uses a lightweight cross-encoder model to rerank candidates
    based on semantic relevance to the query.
    """

    def __init__(self, model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"):
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name, max_length=512)
        logger.info("Cross-encoder loaded")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder.

        Args:
            query: Search query
            candidates: List of candidate results with 'content' field
            top_k: Number of top results to return

        Returns:
            List of top-K candidates sorted by cross-encoder score
        """
        try:
            if not candidates:
                return []

            # Prepare (query, document) pairs
            pairs = [
                [query, candidate.get("content", candidate.get("title", ""))]
                for candidate in candidates
            ]

            # Score pairs
            scores = self.model.predict(pairs)

            # Sort candidates by score
            scored_candidates = [
                {**candidate, "rerank_score": float(scores[i])}
                for i, candidate in enumerate(candidates)
            ]

            scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

            # Return top K
            reranked = scored_candidates[:top_k]

            logger.debug(
                f"Reranked {len(candidates)} candidates to top {len(reranked)}",
                extra={"query": query[:30]}
            )

            return reranked

        except Exception as e:
            logger.error(f"Reranking error: {e}")
            # Fallback: return candidates as-is
            return candidates[:top_k]
