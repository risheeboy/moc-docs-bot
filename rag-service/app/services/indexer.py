import logging
import uuid
import time
import json
from typing import List, Dict, Any, Optional
from app.services.embedder import EmbedderService
from app.services.vision_embedder import VisionEmbedderService
from app.services.vector_store import VectorStoreService
from app.services.text_splitter import HindiAwareTextSplitter
from app.services.s3_client import S3Client
from app.config import settings

logger = logging.getLogger(__name__)


class IndexerService:
    """
    Document indexing: chunking, embedding, and Milvus insertion.

    Handles the full pipeline from document content to indexed vectors.
    """

    def __init__(self):
        self.embedder = EmbedderService()
        self.vision_embedder = VisionEmbedderService()
        self.vector_store = VectorStoreService()
        self.text_splitter = HindiAwareTextSplitter()
        self.s3_client = S3Client()

    def ingest_document(
        self,
        document_id: str,
        title: str,
        source_url: str,
        source_site: str,
        content: str,
        content_type: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Ingest a document: chunk, embed, and index.

        Args:
            document_id: Unique document ID
            title: Document title
            source_url: Source URL
            source_site: Source site domain
            content: Full text content
            content_type: Document type
            language: Language code
            metadata: Additional metadata
            images: List of images extracted from document

        Returns:
            List of Milvus chunk IDs
        """
        try:
            logger.info(
                "Ingesting document",
                extra={
                    "document_id": document_id,
                    "title": title,
                    "language": language
                }
            )

            # Step 1: Split text into chunks
            chunks = self.text_splitter.split_text(content)
            logger.info(f"Created {len(chunks)} chunks")

            # Step 2: Embed chunks
            embeddings = self.embedder.embed_batch(chunks)

            # Step 3: Prepare documents for Milvus
            milvus_documents = []
            chunk_ids = []

            for chunk_idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)

                milvus_doc = {
                    "id": chunk_id,
                    "document_id": document_id,
                    "chunk_index": chunk_idx,
                    "title": title,
                    "content": chunk_text,
                    "source_url": source_url,
                    "source_site": source_site,
                    "language": language,
                    "content_type": content_type,
                    "dense_embedding": embedding["dense"],
                    "metadata_json": json.dumps({
                        "author": metadata.get("author") if metadata else None,
                        "published_date": metadata.get("published_date") if metadata else None,
                        "tags": metadata.get("tags") if metadata else []
                    }),
                    "created_at": int(time.time() * 1000)
                }
                milvus_documents.append(milvus_doc)

            # Step 4: Upsert to Milvus
            self.vector_store.upsert_text(milvus_documents)

            # Step 5: Process images if provided
            if images:
                self._process_images(document_id, images)

            logger.info(
                f"Ingested document with {len(chunk_ids)} chunks",
                extra={"document_id": document_id}
            )

            return chunk_ids

        except Exception as e:
            logger.error(f"Indexing error: {e}", exc_info=True)
            raise

    def _process_images(
        self,
        document_id: str,
        images: List[Dict[str, Any]]
    ) -> None:
        """Process and index images from document."""
        try:
            if not images:
                return

            milvus_images = []

            for img_idx, img_data in enumerate(images):
                try:
                    image_id = str(uuid.uuid4())
                    image_url = img_data.get("url", "")
                    alt_text = img_data.get("alt_text", "")
                    s3_path = img_data.get("s3_path", "")

                    # Embed image
                    if image_url.startswith("http"):
                        # Remote image
                        embedding_result = self.vision_embedder.embed_image_from_url(image_url)
                    else:
                        # Local image from S3
                        embedding_result = self.vision_embedder.embed_image_from_file(image_url)

                    milvus_img = {
                        "id": image_id,
                        "image_url": image_url,
                        "alt_text": alt_text,
                        "source_url": s3_path,
                        "source_site": document_id,  # For linking back
                        "image_embedding": embedding_result["embedding"],
                        "metadata_json": json.dumps({
                            "document_id": document_id,
                            "index": img_idx
                        }),
                        "created_at": int(time.time() * 1000)
                    }
                    milvus_images.append(milvus_img)

                except Exception as e:
                    logger.warning(f"Error processing image {img_idx}: {e}")
                    continue

            # Upsert images to Milvus
            if milvus_images:
                self.vector_store.upsert_images(milvus_images)
                logger.info(f"Processed {len(milvus_images)} images")

        except Exception as e:
            logger.error(f"Image processing error: {e}")
            # Don't fail document ingestion if images fail

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks of a document from Milvus."""
        try:
            self.vector_store.delete_by_document_id(document_id)
            logger.info(f"Deleted document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
