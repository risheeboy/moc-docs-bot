import logging
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class EmbedderService:
    """
    BGE-M3 embeddings: dense vectors, sparse lexical, and ColBERT tokens.

    BGE-M3 is a multilingual embedding model that returns:
    - Dense embeddings (768 dims)
    - Sparse embeddings (lexical weights)
    - ColBERT tokens (for fine-grained matching)
    """

    def __init__(self):
        logger.info(f"Loading embedding model: {settings.rag_embedding_model}")
        self.model = SentenceTransformer(settings.rag_embedding_model)
        logger.info("Embedding model loaded")

    def embed_text(self, text: str) -> Dict:
        """
        Embed text with BGE-M3.

        Returns:
            {
                "dense": [768-dim vector],
                "sparse": {"token_id": weight, ...},
                "colbert": [[token_embeddings]]
            }
        """
        try:
            # Encode with dense output
            dense_embeddings = self.model.encode(text, convert_to_numpy=True)

            # For sparse embeddings, use the model's built-in sparse output
            # BGE-M3 returns format: {"dense": [...], "sparse": {...}}
            embeddings = self.model.encode(
                text,
                return_dense=True,
                return_sparse=True,
                return_colbert=False
            )

            return {
                "dense": embeddings.get("dense", dense_embeddings).tolist(),
                "sparse": embeddings.get("sparse", {}),
                "text": text
            }
        except Exception as e:
            logger.error(f"Embedding error for text: {text[:50]}: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[Dict]:
        """
        Embed multiple texts efficiently.

        Returns:
            List of embedding dicts (same format as embed_text)
        """
        try:
            embeddings_batch = self.model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                return_dense=True,
                return_sparse=True,
                return_colbert=False
            )

            results = []
            for i, text in enumerate(texts):
                embedding_dict = {
                    "dense": embeddings_batch[i].get("dense").tolist()
                    if isinstance(embeddings_batch[i], dict)
                    else embeddings_batch[i].tolist(),
                    "sparse": embeddings_batch[i].get("sparse", {})
                    if isinstance(embeddings_batch[i], dict)
                    else {},
                    "text": text
                }
                results.append(embedding_dict)

            return results
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of dense embeddings."""
        return self.model.get_sentence_embedding_dimension()
