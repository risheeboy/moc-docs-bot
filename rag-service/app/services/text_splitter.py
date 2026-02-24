import logging
import re
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)


class HindiAwareTextSplitter:
    """
    Hindi-aware text chunking that respects sentence boundaries.

    Splits text into chunks of RAG_CHUNK_SIZE with RAG_CHUNK_OVERLAP,
    but respects Hindi sentence boundaries.
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

        # Hindi sentence terminators
        self.hindi_sentence_endings = r'।|\.|!|\?|。|！|？'
        self.english_sentence_endings = r'\.|\?|!'

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting sentence boundaries.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        try:
            # First, split into sentences
            sentences = self._split_into_sentences(text)

            if not sentences:
                return []

            # Then combine sentences into chunks
            chunks = []
            current_chunk = ""

            for sentence in sentences:
                # Add sentence to current chunk
                test_chunk = (current_chunk + " " + sentence).strip()

                # Check if adding this sentence would exceed chunk size
                if len(test_chunk) <= self.chunk_size:
                    current_chunk = test_chunk
                else:
                    # Chunk is full, save it
                    if current_chunk:
                        chunks.append(current_chunk)

                    # Start new chunk with overlap
                    if len(sentence) <= self.chunk_size:
                        current_chunk = sentence
                    else:
                        # Sentence is longer than chunk size, split it
                        sub_chunks = self._split_long_sentence(sentence)
                        chunks.extend(sub_chunks[:-1])
                        current_chunk = sub_chunks[-1]

            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk)

            # Add overlap
            chunks = self._add_overlap(chunks)

            logger.info(
                f"Split text into {len(chunks)} chunks",
                extra={"chunk_size": self.chunk_size, "overlap": self.chunk_overlap}
            )

            return chunks

        except Exception as e:
            logger.error(f"Error splitting text: {e}")
            return [text]

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences by Hindi and English sentence markers."""
        try:
            # Combine all sentence endings
            all_endings = f"({self.hindi_sentence_endings}|{self.english_sentence_endings})"

            # Split by sentence endings, keeping the ending
            parts = re.split(f'(?<={all_endings})\s+', text)

            sentences = []
            for part in parts:
                if part.strip():
                    sentences.append(part.strip())

            return sentences
        except Exception as e:
            logger.warning(f"Error splitting into sentences: {e}")
            return [text]

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a long sentence that exceeds chunk size."""
        try:
            # Split by phrases, spaces, or commas
            words = sentence.split()
            chunks = []
            current = ""

            for word in words:
                test = (current + " " + word).strip()
                if len(test) <= self.chunk_size:
                    current = test
                else:
                    if current:
                        chunks.append(current)
                    current = word

            if current:
                chunks.append(current)

            return chunks
        except Exception as e:
            logger.warning(f"Error splitting long sentence: {e}")
            return [sentence]

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Add overlap between consecutive chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                # Add overlap from previous chunk
                prev_chunk = chunks[i - 1]
                overlap_text = self._extract_overlap(prev_chunk)
                overlapped.append((overlap_text + " " + chunk).strip())

        return overlapped

    def _extract_overlap(self, text: str) -> str:
        """Extract last N tokens from text for overlap."""
        words = text.split()
        # Calculate how many tokens to use for overlap
        overlap_tokens = max(1, self.chunk_overlap // 4)  # Rough estimate
        return " ".join(words[-overlap_tokens:])
