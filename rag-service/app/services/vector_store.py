import logging
from typing import Dict, List, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import time
from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Milvus vector store for text and image embeddings.

    Manages collections for text and image embeddings with hybrid search support.
    """

    def __init__(self):
        self.host = settings.milvus_host
        self.port = settings.milvus_port
        self.text_collection = settings.milvus_collection_text
        self.image_collection = settings.milvus_collection_image
        self._connect()

    def _get_milvus_connection(self):
        """Get or create Milvus connection."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            return connections
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _connect(self):
        """Initialize connection to Milvus."""
        try:
            self._get_milvus_connection()
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Milvus connection error: {e}")
            raise

    def _get_or_create_text_collection(self):
        """Get or create text embeddings collection."""
        try:
            connections.connect(alias="default", host=self.host, port=self.port)

            # Check if collection exists
            if self.text_collection in connections.list_collections():
                return Collection(name=self.text_collection)

            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="chunk_index", dtype=DataType.INT32),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
                FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="source_site", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=10),
                FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="dense_embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
                FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=2048),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]

            schema = CollectionSchema(fields=fields, description="Ministry text embeddings")
            collection = Collection(name=self.text_collection, schema=schema)

            # Create indexes
            collection.create_index(
                field_name="dense_embedding",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 1024}
                }
            )

            logger.info(f"Created collection {self.text_collection}")
            return collection

        except Exception as e:
            logger.error(f"Error creating text collection: {e}")
            raise

    def _get_or_create_image_collection(self):
        """Get or create image embeddings collection."""
        try:
            connections.connect(alias="default", host=self.host, port=self.port)

            # Check if collection exists
            if self.image_collection in connections.list_collections():
                return Collection(name=self.image_collection)

            # Create collection schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
                FieldSchema(name="image_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="alt_text", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="source_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="source_site", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="image_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
                FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]

            schema = CollectionSchema(fields=fields, description="Ministry image embeddings")
            collection = Collection(name=self.image_collection, schema=schema)

            # Create indexes
            collection.create_index(
                field_name="image_embedding",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "L2",
                    "params": {"nlist": 1024}
                }
            )

            logger.info(f"Created collection {self.image_collection}")
            return collection

        except Exception as e:
            logger.error(f"Error creating image collection: {e}")
            raise

    def upsert_text(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Upsert text embeddings into collection.

        Args:
            documents: List of dicts with keys:
                - id, document_id, chunk_index, title, content
                - source_url, source_site, language, content_type
                - dense_embedding, metadata_json, created_at

        Returns:
            List of inserted/updated IDs
        """
        try:
            collection = self._get_or_create_text_collection()

            ids = [doc["id"] for doc in documents]
            collection.upsert(data=documents)
            collection.flush()

            logger.info(f"Upserted {len(documents)} text documents")
            return ids
        except Exception as e:
            logger.error(f"Error upserting text documents: {e}")
            raise

    def upsert_images(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Upsert image embeddings into collection.

        Args:
            documents: List of dicts with image embedding data

        Returns:
            List of inserted/updated IDs
        """
        try:
            collection = self._get_or_create_image_collection()

            ids = [doc["id"] for doc in documents]
            collection.upsert(data=documents)
            collection.flush()

            logger.info(f"Upserted {len(documents)} image documents")
            return ids
        except Exception as e:
            logger.error(f"Error upserting image documents: {e}")
            raise

    def search_text(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Search text embeddings using dense vector similarity.

        Args:
            query_embedding: Query vector (768-dim)
            top_k: Number of results to return
            filters: Optional metadata filters (source_site, language, content_type)

        Returns:
            List of search results with metadata
        """
        try:
            collection = self._get_or_create_text_collection()

            # Build filter expression if provided
            filter_expr = None
            if filters:
                conditions = []
                if filters.get("source_sites"):
                    sites = filters["source_sites"]
                    site_expr = " or ".join([f'source_site == "{site}"' for site in sites])
                    conditions.append(f"({site_expr})")
                if filters.get("language"):
                    conditions.append(f'language == "{filters["language"]}"')
                if filters.get("content_type"):
                    conditions.append(f'content_type == "{filters["content_type"]}"')

                if conditions:
                    filter_expr = " and ".join(conditions)

            # Search
            search_results = collection.search(
                data=[query_embedding],
                anns_field="dense_embedding",
                param={"metric_type": "L2", "params": {"nprobe": 10}},
                limit=top_k,
                expr=filter_expr,
                output_fields=["*"]
            )

            results = []
            for hit in search_results[0]:
                results.append({
                    "id": hit.get("id"),
                    "score": 1.0 - hit.distance / 2,  # Convert L2 distance to similarity
                    "metadata": {
                        "document_id": hit.get("document_id"),
                        "title": hit.get("title"),
                        "content": hit.get("content"),
                        "source_url": hit.get("source_url"),
                        "source_site": hit.get("source_site"),
                        "language": hit.get("language"),
                        "content_type": hit.get("content_type"),
                    }
                })

            return results
        except Exception as e:
            logger.error(f"Error searching text: {e}")
            raise

    def search_images(
        self,
        query_embedding: List[float],
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search image embeddings using vector similarity.

        Args:
            query_embedding: Query vector (384-dim)
            top_k: Number of results to return

        Returns:
            List of search results
        """
        try:
            collection = self._get_or_create_image_collection()

            search_results = collection.search(
                data=[query_embedding],
                anns_field="image_embedding",
                param={"metric_type": "L2", "params": {"nprobe": 10}},
                limit=top_k,
                output_fields=["*"]
            )

            results = []
            for hit in search_results[0]:
                results.append({
                    "id": hit.get("id"),
                    "score": 1.0 - hit.distance / 2,
                    "metadata": {
                        "image_url": hit.get("image_url"),
                        "alt_text": hit.get("alt_text"),
                        "source_url": hit.get("source_url"),
                        "source_site": hit.get("source_site"),
                    }
                })

            return results
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            raise

    def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        try:
            collection = self._get_or_create_text_collection()
            collection.delete(expr=f'document_id == "{document_id}"')
            collection.flush()
            logger.info(f"Deleted document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
