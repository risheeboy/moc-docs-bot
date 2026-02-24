"""Content deduplication using MinHash and SimHash."""

import structlog
from typing import Optional, Tuple
from datasketch import MinHash, MinHashLSH
import hashlib

logger = structlog.get_logger()


class ContentDeduplicator:
    """Deduplicator for detecting duplicate and near-duplicate content."""

    def __init__(
        self,
        num_perm: int = 128,
        threshold: float = 0.95,
    ):
        """Initialize deduplicator.

        Args:
            num_perm: Number of hash functions for MinHash
            threshold: Similarity threshold (0-1) for considering content duplicate
        """
        self.num_perm = num_perm
        self.threshold = threshold

        # Initialize MinHash LSH for efficient similarity search
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.documents = {}  # Map of document_id -> MinHash signature

    def add_document(self, document_id: str, content: str) -> str:
        """Add document to deduplicator.

        Args:
            document_id: Unique document ID
            content: Document content

        Returns:
            Tuple of (is_new, similar_doc_id)
        """
        # Create MinHash signature
        minhash = self._create_minhash(content)
        content_hash = self._hash_content(content)

        # Check if similar content exists
        similar_docs = self.lsh.query(minhash)

        if similar_docs:
            # Found similar document
            for doc_id in similar_docs:
                if doc_id != document_id:
                    similarity = self._calculate_similarity(
                        minhash, self.documents[doc_id]["minhash"]
                    )

                    if similarity >= self.threshold:
                        logger.warning(
                            "duplicate_content_detected",
                            document_id=document_id,
                            similar_to=doc_id,
                            similarity=similarity,
                        )

                        return False, doc_id

        # New document
        self.documents[document_id] = {
            "minhash": minhash,
            "content_hash": content_hash,
            "added_at": None,
        }

        self.lsh.insert(document_id, minhash)

        logger.debug(
            "document_added_to_dedup",
            document_id=document_id,
        )

        return True, None

    def check_duplicate(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check if content is duplicate of existing document.

        Args:
            content: Document content

        Returns:
            Tuple of (is_duplicate, similar_doc_id)
        """
        minhash = self._create_minhash(content)

        similar_docs = self.lsh.query(minhash)

        for doc_id in similar_docs:
            similarity = self._calculate_similarity(
                minhash, self.documents[doc_id]["minhash"]
            )

            if similarity >= self.threshold:
                return True, doc_id

        return False, None

    def remove_document(self, document_id: str) -> bool:
        """Remove document from deduplicator.

        Args:
            document_id: Document ID to remove

        Returns:
            True if removed, False if not found
        """
        if document_id not in self.documents:
            return False

        del self.documents[document_id]
        logger.debug("document_removed_from_dedup", document_id=document_id)

        return True

    @staticmethod
    def _create_minhash(content: str) -> MinHash:
        """Create MinHash signature for content.

        Args:
            content: Text content

        Returns:
            MinHash object
        """
        # Tokenize into words
        tokens = content.lower().split()

        # Create MinHash
        minhash = MinHash(num_perm=128)

        for token in tokens:
            minhash.update(token.encode("utf8"))

        return minhash

    @staticmethod
    def _calculate_similarity(minhash1: MinHash, minhash2: MinHash) -> float:
        """Calculate Jaccard similarity between two MinHashes.

        Args:
            minhash1: First MinHash
            minhash2: Second MinHash

        Returns:
            Similarity score (0-1)
        """
        return minhash1.jaccard(minhash2)

    @staticmethod
    def _hash_content(content: str) -> str:
        """Create SHA256 hash of content.

        Args:
            content: Text content

        Returns:
            Hex hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()


class SimHashDeduplicator:
    """Alternative deduplicator using SimHash for semantic similarity."""

    def __init__(self, threshold: float = 0.95):
        """Initialize SimHash deduplicator.

        Args:
            threshold: Similarity threshold (0-1)
        """
        self.threshold = threshold
        self.documents = {}

    def add_document(self, document_id: str, content: str) -> Tuple[bool, Optional[str]]:
        """Add document to deduplicator.

        Args:
            document_id: Unique document ID
            content: Document content

        Returns:
            Tuple of (is_new, similar_doc_id)
        """
        from simhash import SimHash

        # Create SimHash
        simhash = SimHash(content).value

        # Check for similar documents
        for doc_id, stored_hash in self.documents.items():
            similarity = self._calculate_similarity(simhash, stored_hash)

            if similarity >= self.threshold:
                logger.warning(
                    "similar_content_detected",
                    document_id=document_id,
                    similar_to=doc_id,
                    similarity=similarity,
                )

                return False, doc_id

        # New document
        self.documents[document_id] = simhash

        logger.debug("document_added_to_simhash", document_id=document_id)

        return True, None

    @staticmethod
    def _calculate_similarity(hash1: int, hash2: int) -> float:
        """Calculate Hamming similarity between SimHashes.

        Args:
            hash1: First SimHash value
            hash2: Second SimHash value

        Returns:
            Similarity score (0-1)
        """
        # Count differing bits (Hamming distance)
        xor = hash1 ^ hash2
        ones = bin(xor).count("1")

        # Hamming distance normalized to 0-1
        # (64 bits for SimHash)
        distance = ones / 64.0

        # Convert to similarity (1 - distance)
        return 1.0 - distance
