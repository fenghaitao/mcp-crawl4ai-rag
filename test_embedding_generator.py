"""
Basic test to verify EmbeddingGenerator implementation.

Tests the core functionality of the EmbeddingGenerator class including:
- Batch embedding generation
- Single embedding generation
- Code syntax preservation
- Vector normalization
- Error handling
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from src.user_manual_chunker.embedding_generator import EmbeddingGenerator
from src.user_manual_chunker.interfaces import DocumentChunk
from src.user_manual_chunker.data_models import (
    Section,
    Heading,
    Paragraph,
    CodeBlock
)


def create_test_chunk(content: str, chunk_index: int = 0) -> DocumentChunk:
    """Helper to create a test DocumentChunk."""
    heading = Heading(level=1, text="Test", line_number=1)
    section = Section(heading=heading)
    
    return DocumentChunk(
        content=content,
        section=section,
        chunk_index=chunk_index,
        line_start=1,
        line_end=10
    )


def test_embedding_generator_initialization():
    """Test EmbeddingGenerator initialization with default parameters."""
    gen = EmbeddingGenerator()
    
    assert gen.model == "text-embedding-3-small"
    assert gen.batch_size == 32
    assert gen.normalize is True


def test_embedding_generator_custom_parameters():
    """Test EmbeddingGenerator initialization with custom parameters."""
    gen = EmbeddingGenerator(
        model="custom-model",
        batch_size=16,
        normalize=False
    )
    
    assert gen.model == "custom-model"
    assert gen.batch_size == 16
    assert gen.normalize is False


def test_prepare_text_for_embedding():
    """Test that code syntax is preserved in embedding input."""
    gen = EmbeddingGenerator()
    
    # Create chunk with code block
    content = """# Test Section

Here is some code:

```python
def hello():
    print("Hello")
```

End of section."""
    
    chunk = create_test_chunk(content)
    prepared = gen._prepare_text_for_embedding(chunk)
    
    # Verify code markers are preserved
    assert "```python" in prepared
    assert "def hello():" in prepared
    assert "```" in prepared


def test_normalize_vector():
    """Test vector normalization."""
    gen = EmbeddingGenerator(normalize=True)
    
    # Create a non-normalized vector
    vector = np.array([3.0, 4.0], dtype=np.float32)
    normalized = gen._normalize_vector(vector)
    
    # Check L2 norm is 1.0
    norm = np.linalg.norm(normalized)
    assert abs(norm - 1.0) < 1e-6
    
    # Check direction is preserved
    assert normalized[0] / normalized[1] == pytest.approx(3.0 / 4.0)


def test_normalize_zero_vector():
    """Test normalization of zero vector."""
    gen = EmbeddingGenerator(normalize=True)
    
    # Zero vector should remain zero
    vector = np.zeros(10, dtype=np.float32)
    normalized = gen._normalize_vector(vector)
    
    assert np.allclose(normalized, vector)


def test_normalize_vectors_batch():
    """Test batch vector normalization."""
    gen = EmbeddingGenerator(normalize=True)
    
    vectors = [
        np.array([3.0, 4.0], dtype=np.float32),
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0], dtype=np.float32)
    ]
    
    normalized = gen._normalize_vectors(vectors)
    
    # Check all vectors are normalized
    for vec in normalized:
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-6


@patch('src.user_manual_chunker.embedding_generator.create_embeddings_batch_copilot')
def test_generate_embeddings_batch(mock_batch_embed):
    """Test batch embedding generation."""
    # Mock the Copilot API to return embeddings
    mock_embeddings = [
        [0.1] * 1536,
        [0.2] * 1536,
        [0.3] * 1536
    ]
    mock_batch_embed.return_value = mock_embeddings
    
    gen = EmbeddingGenerator(normalize=False)
    
    chunks = [
        create_test_chunk("Chunk 1", 0),
        create_test_chunk("Chunk 2", 1),
        create_test_chunk("Chunk 3", 2)
    ]
    
    embeddings = gen.generate_embeddings(chunks)
    
    assert len(embeddings) == 3
    assert all(isinstance(emb, np.ndarray) for emb in embeddings)
    assert all(emb.shape == (1536,) for emb in embeddings)
    assert all(emb.dtype == np.float32 for emb in embeddings)


@patch('src.user_manual_chunker.embedding_generator.create_embeddings_batch_copilot')
def test_generate_embeddings_with_normalization(mock_batch_embed):
    """Test that embeddings are normalized when requested."""
    # Mock the Copilot API to return non-normalized embeddings
    mock_embeddings = [
        [3.0, 4.0] + [0.0] * 1534,  # L2 norm = 5.0
        [1.0, 0.0] + [0.0] * 1534   # L2 norm = 1.0
    ]
    mock_batch_embed.return_value = mock_embeddings
    
    gen = EmbeddingGenerator(normalize=True)
    
    chunks = [
        create_test_chunk("Chunk 1", 0),
        create_test_chunk("Chunk 2", 1)
    ]
    
    embeddings = gen.generate_embeddings(chunks)
    
    # Check all embeddings are normalized
    for emb in embeddings:
        norm = np.linalg.norm(emb)
        assert abs(norm - 1.0) < 1e-5


@patch('src.user_manual_chunker.embedding_generator.create_embeddings_batch_copilot')
def test_generate_embeddings_error_handling(mock_batch_embed):
    """Test that errors are logged and processing continues."""
    # Mock the Copilot API to raise an exception
    mock_batch_embed.side_effect = Exception("API Error")
    
    gen = EmbeddingGenerator()
    
    chunks = [
        create_test_chunk("Chunk 1", 0),
        create_test_chunk("Chunk 2", 1)
    ]
    
    # Should not raise exception, but return zero embeddings
    embeddings = gen.generate_embeddings(chunks)
    
    assert len(embeddings) == 2
    # Check that zero embeddings were returned
    for emb in embeddings:
        assert np.allclose(emb, np.zeros(1536, dtype=np.float32))


@patch('src.user_manual_chunker.embedding_generator.create_embedding_copilot')
def test_generate_embedding_single(mock_single_embed):
    """Test single embedding generation."""
    # Mock the Copilot API
    mock_embedding = [0.5] * 1536
    mock_single_embed.return_value = mock_embedding
    
    gen = EmbeddingGenerator(normalize=False)
    chunk = create_test_chunk("Test chunk")
    
    embedding = gen.generate_embedding_single(chunk)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1536,)
    assert embedding.dtype == np.float32


@patch('src.user_manual_chunker.embedding_generator.create_embedding_copilot')
def test_generate_embedding_single_error_handling(mock_single_embed):
    """Test single embedding error handling."""
    # Mock the Copilot API to raise an exception
    mock_single_embed.side_effect = Exception("API Error")
    
    gen = EmbeddingGenerator()
    chunk = create_test_chunk("Test chunk")
    
    # Should not raise exception, but return zero embedding
    embedding = gen.generate_embedding_single(chunk)
    
    assert isinstance(embedding, np.ndarray)
    assert np.allclose(embedding, np.zeros(1536, dtype=np.float32))


@patch('src.user_manual_chunker.embedding_generator.create_embeddings_batch_copilot')
def test_generate_embeddings_empty_list(mock_batch_embed):
    """Test handling of empty chunk list."""
    gen = EmbeddingGenerator()
    
    embeddings = gen.generate_embeddings([])
    
    assert embeddings == []
    # Should not call the API for empty list
    mock_batch_embed.assert_not_called()


@patch('src.user_manual_chunker.embedding_generator.create_embeddings_batch_copilot')
def test_generate_embeddings_batching(mock_batch_embed):
    """Test that chunks are processed in batches."""
    # Mock the Copilot API to return correct number of embeddings per batch
    def side_effect(texts):
        return [[0.1] * 1536] * len(texts)
    
    mock_batch_embed.side_effect = side_effect
    
    gen = EmbeddingGenerator(batch_size=10)
    
    # Create 25 chunks (should be 3 batches: 10, 10, 5)
    chunks = [create_test_chunk(f"Chunk {i}", i) for i in range(25)]
    
    embeddings = gen.generate_embeddings(chunks)
    
    assert len(embeddings) == 25
    # Should have called the API 3 times
    assert mock_batch_embed.call_count == 3


def test_add_embeddings_to_chunks():
    """Test adding embeddings to ProcessedChunk objects."""
    from src.user_manual_chunker.data_models import ProcessedChunk, ChunkMetadata
    
    gen = EmbeddingGenerator()
    
    # Create test chunks and processed chunks
    chunks = [
        create_test_chunk("Chunk 1", 0),
        create_test_chunk("Chunk 2", 1)
    ]
    
    metadata = ChunkMetadata(
        source_file="test.md",
        heading_hierarchy=["Test"],
        section_level=1,
        contains_code=False,
        code_languages=[],
        chunk_index=0,
        line_start=1,
        line_end=10,
        char_count=100
    )
    
    processed_chunks = [
        ProcessedChunk(chunk_id="1", content="Chunk 1", metadata=metadata),
        ProcessedChunk(chunk_id="2", content="Chunk 2", metadata=metadata)
    ]
    
    # Mock the embedding generation
    with patch.object(gen, 'generate_embeddings') as mock_gen:
        mock_gen.return_value = [
            np.array([0.1] * 1536, dtype=np.float32),
            np.array([0.2] * 1536, dtype=np.float32)
        ]
        
        gen.add_embeddings_to_chunks(chunks, processed_chunks)
    
    # Check embeddings were added
    assert processed_chunks[0].embedding is not None
    assert processed_chunks[1].embedding is not None
    assert processed_chunks[0].embedding.shape == (1536,)
    assert processed_chunks[1].embedding.shape == (1536,)


def test_add_embeddings_to_chunks_length_mismatch():
    """Test error handling for mismatched chunk lists."""
    from src.user_manual_chunker.data_models import ProcessedChunk, ChunkMetadata
    
    gen = EmbeddingGenerator()
    
    chunks = [create_test_chunk("Chunk 1", 0)]
    
    metadata = ChunkMetadata(
        source_file="test.md",
        heading_hierarchy=["Test"],
        section_level=1,
        contains_code=False,
        code_languages=[],
        chunk_index=0,
        line_start=1,
        line_end=10,
        char_count=100
    )
    
    processed_chunks = [
        ProcessedChunk(chunk_id="1", content="Chunk 1", metadata=metadata),
        ProcessedChunk(chunk_id="2", content="Chunk 2", metadata=metadata)
    ]
    
    # Should raise ValueError for length mismatch
    with pytest.raises(ValueError, match="Mismatch between chunks"):
        gen.add_embeddings_to_chunks(chunks, processed_chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
