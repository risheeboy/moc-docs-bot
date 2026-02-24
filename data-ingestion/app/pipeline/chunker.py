"""Document chunking and RAG service integration."""

import structlog
import uuid
from typing import List, Dict, Any, Optional

import httpx

from app.config import settings
from app.utils.metrics import chunking_errors_total

logger = structlog.get_logger()


class DocumentChunker:
    """Chunk documents and send to RAG service for embedding."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """Initialize chunker.

        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    async def chunk_document(
        self,
        content: str,
        document_id: str = None,
    ) -> List[Dict[str, Any]]:
        """Chunk document content.

        Args:
            content: Document content
            document_id: Document ID for tracking

        Returns:
            List of chunks with metadata
        """
        if not document_id:
            document_id = str(uuid.uuid4())

        chunks = []

        try:
            # Split by paragraphs first
            paragraphs = content.split("\n\n")

            current_chunk = ""
            chunk_index = 0

            for paragraph in paragraphs:
                # Skip very short paragraphs
                if len(paragraph.strip()) < 10:
                    continue

                # If adding this paragraph exceeds chunk size, save current chunk
                if (
                    len(current_chunk) + len(paragraph)
                    > self.chunk_size
                    and current_chunk
                ):
                    chunks.append(
                        {
                            "chunk_id": f"{document_id}_chunk_{chunk_index}",
                            "content": current_chunk.strip(),
                            "index": chunk_index,
                            "start_char": sum(
                                len(c["content"]) + self.chunk_overlap
                                for c in chunks
                            ),
                        }
                    )

                    chunk_index += 1

                    # Create overlap
                    current_chunk = current_chunk[
                        -self.chunk_overlap :
                    ] + paragraph

                else:
                    current_chunk += "\n\n" + paragraph

            # Add final chunk
            if current_chunk.strip():
                chunks.append(
                    {
                        "chunk_id": f"{document_id}_chunk_{chunk_index}",
                        "content": current_chunk.strip(),
                        "index": chunk_index,
                        "start_char": sum(
                            len(c["content"]) + self.chunk_overlap for c in chunks
                        ),
                    }
                )

            logger.info(
                "document_chunked",
                document_id=document_id,
                chunk_count=len(chunks),
                content_length=len(content),
            )

            return chunks

        except Exception as e:
            logger.error(
                "chunking_error",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            chunking_errors_total.inc()
            return []

    async def chunk_and_ingest(
        self,
        document: Dict[str, Any],
    ) -> Optional[List[str]]:
        """Chunk document and send to RAG service for ingestion.

        Args:
            document: Document dictionary with required fields

        Returns:
            List of chunk IDs or None if ingestion fails
        """
        document_id = document.get("document_id", str(uuid.uuid4()))

        try:
            # Chunk the document
            chunks = await self.chunk_document(
                document.get("content", ""),
                document_id,
            )

            if not chunks:
                logger.warning(
                    "no_chunks_created",
                    document_id=document_id,
                )
                return None

            # Prepare ingestion request per §8.1
            ingest_request = {
                "document_id": document_id,
                "title": document.get("title", ""),
                "source_url": document.get("url", ""),
                "source_site": document.get("source_site", ""),
                "content": document.get("content", ""),
                "content_type": document.get("content_type", "webpage"),
                "language": document.get("language", "en"),
                "metadata": document.get("metadata", {}),
                "images": document.get("images", []),
            }

            # Send to RAG service
            async with httpx.AsyncClient(
                timeout=30.0,
            ) as client:
                response = await client.post(
                    f"{settings.rag_service_url}/ingest",
                    json=ingest_request,
                    headers={
                        "Content-Type": "application/json",
                    },
                )

                response.raise_for_status()

                result = response.json()

                milvus_ids = result.get("milvus_ids", [])

                logger.info(
                    "document_ingested",
                    document_id=document_id,
                    chunk_count=len(chunks),
                    milvus_ids=milvus_ids,
                )

                return milvus_ids

        except Exception as e:
            logger.error(
                "document_ingestion_error",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            chunking_errors_total.inc()
            return None
