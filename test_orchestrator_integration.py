#!/usr/bin/env python3
"""
Integration tests for UserManualChunker orchestrator.

Tests the complete end-to-end pipeline with all components.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.user_manual_chunker import (
    UserManualChunker,
    ChunkerConfig,
)


def test_end_to_end_pipeline():
    """
    Test complete end-to-end pipeline.
    
    Validates Requirements 8.1, 8.2, 8.3, 8.4, 8.5
    """
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    # Create orchestrator with full configuration
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        chunk_overlap=50,
        generate_summaries=False,  # Skip for speed
        generate_embeddings=False  # Skip for speed
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Step 1: Process document
    print(f"\nProcessing document: {sample_doc}")
    chunks = chunker.process_document(sample_doc)
    
    # Validate Requirement 8.1: Structured format with content, metadata, embeddings
    assert len(chunks) > 0, "Should produce at least one chunk"
    
    for chunk in chunks:
        assert chunk.chunk_id is not None, "Chunk should have ID"
        assert chunk.content is not None, "Chunk should have content"
        assert chunk.metadata is not None, "Chunk should have metadata"
        # Note: summary and embedding are None because we disabled them
    
    print(f"✓ Created {len(chunks)} chunks with structured format")
    
    # Validate Requirement 8.2: Unique identifiers
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    unique_ids = set(chunk_ids)
    
    assert len(chunk_ids) == len(unique_ids), "All chunk IDs should be unique"
    print(f"✓ All {len(chunk_ids)} chunk IDs are unique")
    
    # Validate Requirement 8.3: JSON format support
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json_output_path = f.name
    
    try:
        chunker.export_to_json(chunks, json_output_path, include_statistics=True)
        
        # Verify JSON structure
        with open(json_output_path, 'r') as f:
            json_data = json.load(f)
        
        assert "chunks" in json_data, "JSON should have 'chunks' field"
        assert "statistics" in json_data, "JSON should have 'statistics' field"
        assert len(json_data["chunks"]) == len(chunks), "JSON should contain all chunks"
        
        # Verify chunk structure in JSON
        first_chunk_json = json_data["chunks"][0]
        assert "chunk_id" in first_chunk_json
        assert "content" in first_chunk_json
        assert "metadata" in first_chunk_json
        assert "summary" in first_chunk_json
        assert "embedding" in first_chunk_json
        
        print(f"✓ JSON export successful with proper structure")
        
    finally:
        if Path(json_output_path).exists():
            Path(json_output_path).unlink()
    
    # Validate Requirement 8.4: Vector database format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        vector_db_output_path = f.name
    
    try:
        chunker.export_to_vector_db_format(chunks, vector_db_output_path)
        
        # Verify vector DB format
        with open(vector_db_output_path, 'r') as f:
            vector_db_data = json.load(f)
        
        assert isinstance(vector_db_data, list), "Vector DB format should be a list"
        assert len(vector_db_data) == len(chunks), "Should contain all chunks"
        
        # Verify record structure
        first_record = vector_db_data[0]
        assert "id" in first_record
        assert "content" in first_record
        assert "metadata" in first_record
        assert "summary" in first_record
        assert "embedding" in first_record
        
        print(f"✓ Vector DB format export successful")
        
    finally:
        if Path(vector_db_output_path).exists():
            Path(vector_db_output_path).unlink()
    
    # Validate Requirement 8.5: Processing statistics
    stats = chunker.get_statistics()
    
    assert stats["total_chunks"] == len(chunks), "Statistics should track chunk count"
    assert stats["average_chunk_size"] > 0, "Statistics should track average size"
    assert stats["processing_time_seconds"] > 0, "Statistics should track processing time"
    
    # Verify statistics accuracy
    total_chars = sum(chunk.metadata.char_count for chunk in chunks)
    expected_avg = total_chars / len(chunks)
    
    assert abs(stats["average_chunk_size"] - expected_avg) < 1.0, \
        "Average chunk size should be accurate"
    
    print(f"✓ Statistics tracking accurate:")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Average size: {stats['average_chunk_size']:.1f} chars")
    print(f"  - Processing time: {stats['processing_time_seconds']:.3f}s")
    
    print("\n✓ All requirements validated successfully!")


def test_metadata_completeness():
    """
    Test that metadata extraction is complete.
    
    Validates Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    # Create orchestrator
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    # Process document
    chunks = chunker.process_document(sample_doc)
    
    # Verify metadata for each chunk
    for chunk in chunks:
        metadata = chunk.metadata
        
        # Requirement 2.1: Heading hierarchy
        assert isinstance(metadata.heading_hierarchy, list), \
            "Heading hierarchy should be a list"
        
        # Requirement 2.2: Source file path
        assert metadata.source_file == sample_doc, \
            "Source file should be recorded"
        
        # Requirement 2.3: Code language detection (if code present)
        if metadata.contains_code:
            assert isinstance(metadata.code_languages, list), \
                "Code languages should be a list"
        
        # Requirement 2.4: Code presence flag
        assert isinstance(metadata.contains_code, bool), \
            "Contains code should be a boolean"
        
        # Requirement 2.5: Section level
        assert metadata.section_level > 0, \
            "Section level should be positive"
        assert metadata.section_level == len(metadata.heading_hierarchy), \
            "Section level should match hierarchy depth"
    
    print(f"\n✓ Metadata completeness validated for {len(chunks)} chunks")


def test_chunk_content_integrity():
    """
    Test that chunk content maintains integrity.
    
    Validates Requirements 1.2, 1.4 (code block integrity)
    """
    # Find a sample document with code
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    # Process multiple documents to find one with code
    config = ChunkerConfig(
        generate_summaries=False,
        generate_embeddings=False
    )
    
    chunker = UserManualChunker.from_config(config)
    
    chunks_with_code = []
    
    for doc in sample_docs[:5]:  # Check first 5 documents
        chunks = chunker.process_document(str(doc))
        chunks_with_code.extend([c for c in chunks if c.metadata.contains_code])
        
        if len(chunks_with_code) >= 3:
            break
    
    if not chunks_with_code:
        pytest.skip("No chunks with code found")
    
    # Verify code block integrity
    for chunk in chunks_with_code:
        content = chunk.content
        
        # Count code fences
        fence_count = content.count("```")
        
        # Code fences should be balanced (even number)
        assert fence_count % 2 == 0, \
            f"Code fences should be balanced in chunk {chunk.chunk_id}"
        
        # If there are code blocks, verify they're complete
        if fence_count > 0:
            # Split by code fences
            parts = content.split("```")
            
            # Should have odd number of parts (text, code, text, code, ...)
            assert len(parts) % 2 == 1, \
                f"Code blocks should be complete in chunk {chunk.chunk_id}"
    
    print(f"\n✓ Code block integrity validated for {len(chunks_with_code)} chunks with code")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
