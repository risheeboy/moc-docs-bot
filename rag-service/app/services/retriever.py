import logging
from typing import List, Dict, Any, Optional
import json
from app.services.embedder import EmbedderService
from app.services.vector_store import VectorStoreService
from app.services.reranker import RerankerService
from app.config import settings

logger = logging.getLogger(__name__)


class RetrieverService:
    """
    Hybrid retrieval using BGE-M3 dense embeddings and Milvus.

    Combines dense vector search with optional reranking for better results.
    """

    def __init__(self):
        self.embedder = EmbedderService()
        self.vector_store = VectorStoreService()
        self.reranker = RerankerService()

    def retrieve(
        self,
        query: str,
        language: str,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Steps:
        1. Embed query with BGE-M3
        2. Search Milvus for similar chunks
        3. Rerank results with cross-encoder
        4. Return top-K results

        Args:
            query: User query
            language: Language code
            top_k: Initial retrieval count
            rerank_top_k: Final result count after reranking
            filters: Optional metadata filters

        Returns:
            List of retrieved chunks with metadata and scores
        """
        try:
            logger.info(
                f"Retrieving documents for query: {query[:50]}",
                extra={"language": language, "top_k": top_k}
            )

            # Step 1: Embed query
            query_embedding = self.embedder.embed_text(query)

            # Step 2: Search Milvus
            milvus_filters = {}
            if filters:
                if filters.get("source_sites"):
                    milvus_filters["source_sites"] = filters["source_sites"]
                if filters.get("content_type"):
                    milvus_filters["content_type"] = filters["content_type"]
                if language:
                    milvus_filters["language"] = language

            search_results = self.vector_store.search_text(
                query_embedding=query_embedding["dense"],
                top_k=top_k * 2,  # Over-retrieve for reranking
                filters=milvus_filters
            )

            if not search_results:
                logger.warning("No documents found in Milvus")
                return []

            # Step 3: Rerank results
            candidates = []
            for result in search_results:
                candidates.append({
                    "chunk_id": result["id"],
                    "score": result["score"],
                    "title": result["metadata"].get("title", ""),
                    "content": result["metadata"].get("content", ""),
                    "url": result["metadata"].get("source_url", ""),
                    "source_site": result["metadata"].get("source_site", ""),
                    "language": result["metadata"].get("language", language),
                    "content_type": result["metadata"].get("content_type", ""),
                })

            # Rerank if we have a reranker
            if rerank_top_k > 0:
                reranked = self.reranker.rerank(
                    query=query,
                    candidates=candidates,
                    top_k=rerank_top_k
                )
            else:
                reranked = candidates[:rerank_top_k]

            # Build final results with snippets
            final_results = []
            for candidate in reranked:
                # Generate snippet from content
                content = candidate["content"]
                snippet = self._generate_snippet(content, query)

                final_results.append({
                    "chunk_id": candidate["chunk_id"],
                    "title": candidate["title"],
                    "url": candidate["url"],
                    "snippet": snippet,
                    "score": candidate["score"],
                    "source_site": candidate["source_site"],
                    "language": candidate["language"],
                    "content_type": candidate["content_type"],
                })

            logger.info(
                f"Retrieved {len(final_results)} documents",
                extra={"query": query[:30]}
            )

            return final_results

        except Exception as e:
            logger.error(f"Retrieval error: {e}", exc_info=True)
            raise

    def _generate_snippet(self, content: str, query: str, max_length: int = 300) -> str:
        """
        Generate a snippet from content highlighting the query.

        Simple implementation: find first occurrence of query term and extract context.
        """
        try:
            # Find query position
            lower_content = content.lower()
            lower_query = query.lower()

            pos = lower_content.find(lower_query)
            if pos < 0:
                # Query not found, return beginning
                return content[:max_length].strip()

            # Extract context around match
            start = max(0, pos - 50)
            end = min(len(content), pos + max_length - 50)

            snippet = content[start:end].strip()
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."

            return snippet[:max_length]
        except Exception as e:
            logger.warning(f"Error generating snippet: {e}")
            return content[:max_length].strip()
