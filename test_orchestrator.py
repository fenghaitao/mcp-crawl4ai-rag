#!/usr/bin/env python3
"""
Tests for UserManualChunker orchestrator.

Tests the main orchestrator functionality including document processing,
JSON export, and statistics tracking.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.user_manual_chunker import (
    UserManualChunker,
    ChunkerConfig,
    MarkdownParser,
    SemanticChunker,
    MetadataExtractor,
)


def test_orchestrator_initialization():
    """Test that orchestrator can be initialized with default config."""
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    assert chunker is not None
    assert chunker.config == config
    assert chunker.parser is not None
    assert chunker.chunker is not None
    assert chunker.metadata_extractor is not None


def test_orchestrator_process_document():
    """Test processing a single document."""
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    # Create orchestrator
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Process document
    chunks = chunker.process_document(sample_doc)
    
    # Verify results
    assert len(chunks) > 0
    
    # Check first chunk
    first_chunk = chunks[0]
    assert first_chunk.chunk_id is not None
    assert len(first_chunk.chunk_id) > 0
    assert first_chunk.content is not None
    assert len(first_chunk.content) > 0
    assert first_chunk.metadata is not None
    assert first_chunk.metadata.source_file == sample_doc
    
    # Verify statistics
    stats = chunker.get_statistics()
    assert stats["total_chunks"] == len(chunks)
    assert stats["processing_time_seconds"] > 0


def test_chunk_id_uniqueness():
    """Test that chunk IDs are unique across documents."""
    # Find sample documents
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))[:2]
    
    if len(sample_docs) < 2:
        pytest.skip("Need at least 2 documents for this test")
    
    # Create orchestrator
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Process documents and collect chunk IDs
    all_chunk_ids = []
    
    for doc in sample_docs:
        chunks = chunker.process_document(str(doc))
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        all_chunk_ids.extend(chunk_ids)
    
    # Verify uniqueness
    assert len(all_chunk_ids) == len(set(all_chunk_ids)), "Chunk IDs are not unique"


def test_json_export():
    """Test JSON export functionality."""
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    # Create orchestrator and process document
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    chunks = chunker.process_document(sample_doc)
    
    # Export to JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        chunker.export_to_json(chunks, output_path, include_statistics=True)
        
        # Verify file exists
        assert Path(output_path).exists()
        
        # Load and verify structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "chunks" in data
        assert "statistics" in data
        assert len(data["chunks"]) == len(chunks)
        
        # Verify first chunk structure
        first_chunk_data = data["chunks"][0]
        assert "chunk_id" in first_chunk_data
        assert "content" in first_chunk_data
        assert "metadata" in first_chunk_data
        assert "summary" in first_chunk_data
        assert "embedding" in first_chunk_data
        
    finally:
        # Clean up
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_vector_db_export():
    """Test vector database format export."""
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    # Create orchestrator and process document
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    chunks = chunker.process_document(sample_doc)
    
    # Export to vector DB format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        chunker.export_to_vector_db_format(chunks, output_path)
        
        # Verify file exists
        assert Path(output_path).exists()
        
        # Load and verify structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == len(chunks)
        
        # Verify first record structure
        first_record = data[0]
        assert "id" in first_record
        assert "content" in first_record
        assert "metadata" in first_record
        assert "summary" in first_record
        assert "embedding" in first_record
        
    finally:
        # Clean up
        if Path(output_path).exists():
            Path(output_path).unlink()


def test_statistics_tracking():
    """Test that statistics are tracked correctly."""
    # Find sample documents
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))[:2]
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    # Create orchestrator
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Reset statistics
    chunker.reset_statistics()
    
    # Process documents
    total_chunks = 0
    for doc in sample_docs:
        chunks = chunker.process_document(str(doc))
        total_chunks += len(chunks)
    
    # Verify statistics
    stats = chunker.get_statistics()
    
    assert stats["total_chunks"] == total_chunks
    assert stats["processing_time_seconds"] > 0
    assert stats["average_chunk_size"] > 0
    
    # Test reset
    chunker.reset_statistics()
    stats = chunker.get_statistics()
    
    assert stats["total_chunks"] == 0
    assert stats["processing_time_seconds"] == 0.0
    assert stats["average_chunk_size"] == 0.0


def test_process_nonexistent_file():
    """Test that processing a nonexistent file raises FileNotFoundError."""
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    with pytest.raises(FileNotFoundError):
        chunker.process_document("nonexistent_file.md")


def test_process_directory():
    """Test processing a directory of documents."""
    directory = "pipeline_output/downloaded_pages"
    
    if not Path(directory).exists():
        pytest.skip("Sample directory not found")
    
    # Create orchestrator
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Process directory (limit to first 3 files for speed)
    md_files = list(Path(directory).glob("*.md"))[:3]
    
    if not md_files:
        pytest.skip("No markdown files found")
    
    # Process each file manually (simulating directory processing)
    all_chunks = []
    for file_path in md_files:
        chunks = chunker.process_document(str(file_path))
        all_chunks.extend(chunks)
    
    # Verify results
    assert len(all_chunks) > 0
    
    # Verify statistics
    stats = chunker.get_statistics()
    assert stats["total_chunks"] == len(all_chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
