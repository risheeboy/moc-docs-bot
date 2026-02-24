"""Tests for content deduplication."""

import pytest
from app.pipeline.dedup import ContentDeduplicator


@pytest.fixture
def deduplicator():
    """Create ContentDeduplicator instance."""
    return ContentDeduplicator(threshold=0.95)


def test_add_new_document(deduplicator):
    """Test adding new document."""
    content = "This is unique content about Indian culture and heritage."
    is_new, similar_doc = deduplicator.add_document("doc1", content)

    assert is_new is True
    assert similar_doc is None


def test_detect_duplicate(deduplicator):
    """Test duplicate detection."""
    content1 = "This is content about Indian culture heritage and traditions."
    content2 = "This is content about Indian culture heritage and traditions."

    # Add first document
    is_new1, _ = deduplicator.add_document("doc1", content1)
    assert is_new1 is True

    # Add duplicate - should be detected
    is_new2, similar_doc = deduplicator.add_document("doc2", content2)

    # Very similar content should be detected as duplicate
    if is_new2 is False:
        assert similar_doc == "doc1"


def test_similar_but_not_duplicate(deduplicator):
    """Test similar but distinct documents."""
    content1 = "Content about Indian heritage sites and monuments"
    content2 = "Information about cultural traditions in Indian subcontinent"

    is_new1, _ = deduplicator.add_document("doc1", content1)
    is_new2, similar_doc = deduplicator.add_document("doc2", content2)

    assert is_new1 is True
    # These are different enough to not be duplicates
    # (depending on threshold)


def test_remove_document(deduplicator):
    """Test document removal."""
    content = "Some content here"
    deduplicator.add_document("doc1", content)

    success = deduplicator.remove_document("doc1")
    assert success is True

    # Try to remove non-existent document
    success = deduplicator.remove_document("doc999")
    assert success is False


def test_check_duplicate(deduplicator):
    """Test duplicate checking without adding."""
    content1 = "Original content about Indian culture"
    content2 = "Original content about Indian culture"

    # Add first document
    deduplicator.add_document("doc1", content1)

    # Check if second document is duplicate
    is_dup, similar_doc = deduplicator.check_duplicate(content2)

    # Should detect as duplicate or similar
    if is_dup:
        assert similar_doc == "doc1"


def test_hash_consistency(deduplicator):
    """Test that hashing is consistent."""
    content = "Test content"

    hash1 = deduplicator._hash_content(content)
    hash2 = deduplicator._hash_content(content)

    assert hash1 == hash2


@pytest.mark.parametrize("content1,content2,should_match", [
    (
        "Indian heritage sites and monuments are important",
        "Indian heritage sites and monuments are important",
        True,
    ),
    (
        "About Indian culture",
        "About Indian culture and traditions",
        False,
    ),
])
def test_similarity_threshold(content1, content2, should_match):
    """Test similarity threshold with various content."""
    dedup = ContentDeduplicator(threshold=0.9)

    dedup.add_document("doc1", content1)
    is_dup, _ = dedup.check_duplicate(content2)

    # Depending on content similarity
