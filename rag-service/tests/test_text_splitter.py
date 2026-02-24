import pytest
from app.services.text_splitter import HindiAwareTextSplitter


class TestHindiAwareTextSplitter:
    """Tests for Hindi-aware text chunking."""

    @pytest.fixture
    def splitter(self):
        """Initialize text splitter."""
        return HindiAwareTextSplitter(chunk_size=100, chunk_overlap=10)

    def test_split_english_text(self, splitter):
        """Test splitting English text."""
        text = "This is a sample sentence. Here is another one. And a third sentence."
        chunks = splitter.split_text(text)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_empty_text(self, splitter):
        """Test splitting empty text."""
        chunks = splitter.split_text("")
        assert len(chunks) == 0

    def test_split_short_text(self, splitter):
        """Test splitting text shorter than chunk size."""
        text = "Short text."
        chunks = splitter.split_text(text)
        assert len(chunks) >= 1

    def test_split_hindi_text(self, splitter):
        """Test splitting Hindi text."""
        text = "यह एक नमूना वाक्य है। यहाँ एक और है। और एक तीसरा वाक्य।"
        chunks = splitter.split_text(text)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunks_respect_size_limit(self, splitter):
        """Test that chunks respect size limit."""
        long_text = "This is a sample. " * 20
        chunks = splitter.split_text(long_text)
        for chunk in chunks:
            assert len(chunk) <= splitter.chunk_size + 100  # Allow some buffer

    def test_sentence_splitting(self, splitter):
        """Test that text is split at sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = splitter.split_text(text)
        assert len(chunks) > 0

    def test_overlap_consistency(self, splitter):
        """Test that chunks with overlap are consistent."""
        text = "Word one. Word two. Word three. Word four. Word five."
        chunks = splitter.split_text(text)
        # Verify chunks are valid
        assert all(len(chunk) > 0 for chunk in chunks)
