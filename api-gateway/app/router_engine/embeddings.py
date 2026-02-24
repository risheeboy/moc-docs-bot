"""Lightweight embeddings for semantic router query classification."""

import logging

logger = logging.getLogger(__name__)


class RouterEmbeddings:
    """Embeddings for classifying queries to routes."""

    def __init__(self):
        """Initialize embeddings (lazy load)."""
        self.model = None

    def _ensure_loaded(self):
        """Lazy load embeddings model."""
        if self.model is None:
            try:
                # For production, use sentence-transformers
                # from sentence_transformers import SentenceTransformer
                # self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                pass
            except ImportError:
                logger.warning("sentence-transformers not installed, using mock embeddings")

    def encode(self, text: str) -> list[float]:
        """Encode text to embedding vector."""
        self._ensure_loaded()

        # For now, return mock embedding (32 dimensions)
        # In production, use actual model
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        embedding = []
        for i in range(32):
            val = (hash_int >> i) & 1
            embedding.append(float(val))

        return embedding

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a ** 2 for a in vec1) ** 0.5
        norm2 = sum(b ** 2 for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
