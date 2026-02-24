"""Milvus vector database client helper."""

from typing import Any, Optional
from pymilvus import MilvusClient as PyMilvusClient
import logging

logger = logging.getLogger(__name__)


class MilvusClient:
    """Helper for Milvus vector database operations."""

    def __init__(self, uri: str, db_name: str = "default"):
        """Initialize Milvus client.

        Args:
            uri: Milvus server URI (e.g., http://milvus:19530)
            db_name: Database name to use
        """
        self.uri = uri
        self.db_name = db_name
        self.client: Optional[PyMilvusClient] = None

    def connect(self) -> None:
        """Connect to Milvus server."""
        try:
            self.client = PyMilvusClient(uri=self.uri, db_name=self.db_name)
            logger.info(f"Connected to Milvus at {self.uri} (db={self.db_name})")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def disconnect(self) -> None:
        """Close Milvus connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Milvus")

    def health_check(self) -> bool:
        """Check Milvus connection health.

        Returns:
            True if Milvus is healthy
        """
        try:
            if self.client:
                # Try to get databases
                self.client.list_collections()
                return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
        return False

    def search(
        self,
        collection_name: str,
        data: list[list[float]],
        anns_field: str = "embeddings",
        search_params: Optional[dict[str, Any]] = None,
        limit: int = 10,
        output_fields: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors.

        Args:
            collection_name: Collection to search
            data: Query vectors
            anns_field: Vector field name
            search_params: Search parameters
            limit: Maximum results per query
            output_fields: Fields to return

        Returns:
            Search results
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        if search_params is None:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        try:
            results = self.client.search(
                collection_name=collection_name,
                data=data,
                anns_field=anns_field,
                search_params=search_params,
                limit=limit,
                output_fields=output_fields,
            )
            return results
        except Exception as e:
            logger.error(f"Milvus search failed: {e}")
            raise

    def insert(
        self,
        collection_name: str,
        data: list[dict[str, Any]],
    ) -> list[int]:
        """Insert vectors into collection.

        Args:
            collection_name: Target collection
            data: Documents to insert

        Returns:
            List of inserted IDs
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        try:
            res = self.client.insert(
                collection_name=collection_name,
                data=data,
            )
            return res.get("insert_count", 0)
        except Exception as e:
            logger.error(f"Milvus insert failed: {e}")
            raise

    def delete(
        self,
        collection_name: str,
        filter_expr: str,
    ) -> int:
        """Delete documents from collection.

        Args:
            collection_name: Target collection
            filter_expr: Filter expression

        Returns:
            Number of deleted documents
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        try:
            res = self.client.delete(
                collection_name=collection_name,
                filter=filter_expr,
            )
            return res.get("delete_count", 0)
        except Exception as e:
            logger.error(f"Milvus delete failed: {e}")
            raise

    def query(
        self,
        collection_name: str,
        filter_expr: str,
        output_fields: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query collection with filters.

        Args:
            collection_name: Target collection
            filter_expr: Filter expression
            output_fields: Fields to return
            limit: Maximum results

        Returns:
            Query results
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        try:
            results = self.client.query(
                collection_name=collection_name,
                filter=filter_expr,
                output_fields=output_fields,
                limit=limit,
            )
            return results
        except Exception as e:
            logger.error(f"Milvus query failed: {e}")
            raise

    def list_collections(self) -> list[str]:
        """Get list of all collections.

        Returns:
            Collection names
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        try:
            return self.client.list_collections()
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise

    def __enter__(self) -> "MilvusClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()
