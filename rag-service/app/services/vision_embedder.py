import logging
from typing import Dict, List
import numpy as np
from PIL import Image
import io
import requests
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)


class VisionEmbedderService:
    """
    SigLIP vision embeddings for multimodal search.

    SigLIP provides image embeddings in the same embedding space as text,
    enabling cross-modal search (text→image retrieval).
    """

    def __init__(self):
        logger.info(f"Loading vision model: {settings.rag_vision_embedding_model}")
        self.model = SentenceTransformer(settings.rag_vision_embedding_model)
        logger.info("Vision model loaded")

    def embed_image_from_file(self, image_path: str) -> Dict:
        """
        Embed an image from local file path.

        Args:
            image_path: Local file path to image

        Returns:
            {
                "embedding": [384-dim vector],
                "path": image_path
            }
        """
        try:
            image = Image.open(image_path).convert("RGB")
            embedding = self.model.encode(image, convert_to_numpy=True)
            return {
                "embedding": embedding.tolist(),
                "path": image_path
            }
        except Exception as e:
            logger.error(f"Error embedding image {image_path}: {e}")
            raise

    def embed_image_from_url(self, image_url: str) -> Dict:
        """
        Embed an image from URL.

        Args:
            image_url: URL to image

        Returns:
            {
                "embedding": [384-dim vector],
                "url": image_url
            }
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            embedding = self.model.encode(image, convert_to_numpy=True)
            return {
                "embedding": embedding.tolist(),
                "url": image_url
            }
        except Exception as e:
            logger.error(f"Error embedding image from URL {image_url}: {e}")
            raise

    def embed_image_from_bytes(self, image_bytes: bytes) -> Dict:
        """
        Embed an image from raw bytes.

        Args:
            image_bytes: Raw image bytes

        Returns:
            {
                "embedding": [384-dim vector],
            }
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            embedding = self.model.encode(image, convert_to_numpy=True)
            return {
                "embedding": embedding.tolist()
            }
        except Exception as e:
            logger.error(f"Error embedding image from bytes: {e}")
            raise

    def embed_images_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Embed multiple images efficiently.

        Args:
            image_paths: List of local file paths

        Returns:
            List of embedding dicts
        """
        try:
            images = []
            valid_paths = []
            for path in image_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    images.append(img)
                    valid_paths.append(path)
                except Exception as e:
                    logger.warning(f"Skipping image {path}: {e}")

            if not images:
                return []

            embeddings = self.model.encode(images, batch_size=16, convert_to_numpy=True)

            results = []
            for i, path in enumerate(valid_paths):
                results.append({
                    "embedding": embeddings[i].tolist(),
                    "path": path
                })

            return results
        except Exception as e:
            logger.error(f"Batch image embedding error: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of image embeddings."""
        return self.model.get_sentence_embedding_dimension()
