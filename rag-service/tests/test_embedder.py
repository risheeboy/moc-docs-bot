import pytest
from app.services.embedder import EmbedderService


class TestEmbedderService:
    """Tests for BGE-M3 embedding service."""

    @pytest.fixture
    def embedder(self):
        """Initialize embedder."""
        return EmbedderService()

    def test_embedder_initialization(self, embedder):
        """Test that embedder initializes successfully."""
        assert embedder.model is not None

    def test_embed_text_returns_dict(self, embedder):
        """Test that embed_text returns proper dict structure."""
        text = "This is a sample text."
        result = embedder.embed_text(text)
        assert "dense" in result
        assert "text" in result
        assert isinstance(result["dense"], list)

    def test_embed_text_produces_vector(self, embedder):
        """Test that embedding produces a vector."""
        text = "Test text"
        result = embedder.embed_text(text)
        embedding = result["dense"]
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_hindi_text(self, embedder):
        """Test embedding Hindi text."""
        text = "यह एक परीक्षण पाठ है।"
        result = embedder.embed_text(text)
        assert "dense" in result
        assert isinstance(result["dense"], list)
        assert len(result["dense"]) > 0

    def test_embed_batch_returns_list(self, embedder):
        """Test that embed_batch returns list."""
        texts = [
            "First text",
            "Second text",
            "Third text"
        ]
        results = embedder.embed_batch(texts)
        assert len(results) == len(texts)
        assert all("dense" in result for result in results)

    def test_embedding_dimension(self, embedder):
        """Test that embedding dimension is consistent."""
        dim = embedder.get_embedding_dimension()
        assert dim > 0

        result = embedder.embed_text("Test")
        assert len(result["dense"]) == dim

    def test_similar_texts_have_similar_embeddings(self, embedder):
        """Test that similar texts have similar embeddings."""
        import numpy as np

        text1 = "The cat is on the mat"
        text2 = "A cat sits on the mat"
        text3 = "The weather is sunny today"

        emb1 = np.array(embedder.embed_text(text1)["dense"])
        emb2 = np.array(embedder.embed_text(text2)["dense"])
        emb3 = np.array(embedder.embed_text(text3)["dense"])

        # Normalize
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        emb3 = emb3 / np.linalg.norm(emb3)

        # Similarity between similar texts should be higher
        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)

        assert sim_12 > sim_13  # text1 and text2 are more similar
