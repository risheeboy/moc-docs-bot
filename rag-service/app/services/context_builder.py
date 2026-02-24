import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Assemble retrieved chunks into coherent context for LLM generation.

    Combines snippets with proper citations and source attribution.
    """

    def __init__(self, max_context_length: int = 3000):
        self.max_context_length = max_context_length

    def build_context(
        self,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context string and source metadata from retrieved chunks.

        Args:
            retrieved_chunks: List of chunks from retriever

        Returns:
            (context_text, sources_list)
        """
        try:
            if not retrieved_chunks:
                return "", []

            # Build context with citations
            context_parts = []
            sources = []

            for i, chunk in enumerate(retrieved_chunks):
                # Add snippet with source marker
                snippet = chunk.get("snippet", "")
                title = chunk.get("title", "Untitled")
                source_marker = f"[Source {i + 1}]"

                if snippet:
                    context_parts.append(f"{source_marker} {snippet}")

                # Add to sources list
                sources.append({
                    "title": title,
                    "url": chunk.get("url", ""),
                    "snippet": snippet,
                    "score": chunk.get("score", 0.0),
                    "source_site": chunk.get("source_site", ""),
                    "language": chunk.get("language", ""),
                    "content_type": chunk.get("content_type", ""),
                    "chunk_id": chunk.get("chunk_id", ""),
                })

            # Join context with proper formatting
            context = "\n\n".join(context_parts)

            # Truncate if too long
            if len(context) > self.max_context_length:
                context = context[:self.max_context_length] + "..."

            logger.debug(
                f"Built context from {len(sources)} sources",
                extra={"context_length": len(context)}
            )

            return context, sources

        except Exception as e:
            logger.error(f"Error building context: {e}")
            return "", []
