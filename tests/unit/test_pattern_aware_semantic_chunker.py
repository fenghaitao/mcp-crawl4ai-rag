#!/usr/bin/env python3
"""
Tests for PatternAwareSemanticChunker.

Tests the integration of pattern detection with semantic chunking.
"""

import pytest
from pathlib import Path

from src.user_manual_chunker import (
    PatternAwareSemanticChunker,
    SemanticChunkerImpl as SemanticChunker,
    MarkdownParser,
    ChunkerConfig,
)


def test_pattern_aware_chunker_initialization():
    """Test that pattern-aware chunker can be initialized."""
    chunker = PatternAwareSemanticChunker(
        max_chunk_size=1000,
        min_chunk_size=100,
        enable_pattern_detection=True
    )
    
    assert chunker is not None
    assert chunker.enable_pattern_detection is True
    assert chunker.pattern_analyzer is not None


def test_pattern_aware_chunker_from_config():
    """Test creating pattern-aware chunker from config."""
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100
    )
    
    chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    
    assert chunker is not None
    assert chunker.max_chunk_size == 1000
    assert chunker.min_chunk_size == 100
    assert chunker.enable_pattern_detection is True


def test_pattern_detection_can_be_disabled():
    """Test that pattern detection can be disabled."""
    chunker = PatternAwareSemanticChunker(
        max_chunk_size=1000,
        enable_pattern_detection=False
    )
    
    assert chunker.enable_pattern_detection is False
    assert chunker.pattern_analyzer is None


def test_chunk_document_with_patterns_enabled():
    """Test chunking with pattern detection enabled."""
    content = """
# Test Document

## Section 1

This is a paragraph with some text.

```python
def hello():
    print("Hello")
```

## Section 2

Another paragraph here.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    config = ChunkerConfig(max_chunk_size=500, min_chunk_size=50)
    chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)


def test_chunk_document_with_patterns_disabled():
    """Test chunking with pattern detection disabled."""
    content = """
# Test Document

## Section 1

This is a paragraph with some text.

```python
def hello():
    print("Hello")
```

## Section 2

Another paragraph here.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    config = ChunkerConfig(max_chunk_size=500, min_chunk_size=50)
    chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=False)
    
    chunks = chunker.chunk_document(doc)
    
    assert len(chunks) > 0
    assert all(chunk.content for chunk in chunks)


def test_pattern_statistics():
    """Test getting pattern statistics."""
    content = """
# Test Document

Some content here.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    chunker = PatternAwareSemanticChunker(enable_pattern_detection=True)
    chunks = chunker.chunk_document(doc)
    
    stats = chunker.get_pattern_statistics()
    
    assert isinstance(stats, dict)
    assert 'lists' in stats
    assert 'api_docs' in stats
    assert 'grammar_rules' in stats
    assert 'definitions' in stats
    assert 'tables' in stats
    assert 'references' in stats
    assert 'total' in stats


def test_pattern_statistics_when_disabled():
    """Test pattern statistics when detection is disabled."""
    content = """
# Test Document

Some content here.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    chunker = PatternAwareSemanticChunker(enable_pattern_detection=False)
    chunks = chunker.chunk_document(doc)
    
    stats = chunker.get_pattern_statistics()
    
    # Should return zeros when disabled
    assert stats['total'] == 0
    assert all(count == 0 for count in stats.values())


def test_inherits_from_semantic_chunker():
    """Test that PatternAwareSemanticChunker inherits from SemanticChunker."""
    chunker = PatternAwareSemanticChunker()
    
    assert isinstance(chunker, SemanticChunker)


def test_compatible_with_semantic_chunker_interface():
    """Test that it's compatible with SemanticChunker interface."""
    content = """
# Test Document

Some content here.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Should work the same as SemanticChunker
    regular_chunker = SemanticChunker()
    pattern_chunker = PatternAwareSemanticChunker(enable_pattern_detection=False)
    
    regular_chunks = regular_chunker.chunk_document(doc)
    pattern_chunks = pattern_chunker.chunk_document(doc)
    
    # Should produce same number of chunks when patterns disabled
    assert len(regular_chunks) == len(pattern_chunks)


def test_with_real_document():
    """Test with a real Simics documentation file."""
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        pytest.skip("No sample documents found")
    
    sample_doc = str(sample_docs[0])
    
    with open(sample_doc, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parser = MarkdownParser()
    doc = parser.parse(content, sample_doc)
    
    config = ChunkerConfig(max_chunk_size=1000, min_chunk_size=100)
    
    # Test with patterns enabled
    pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    pattern_chunks = pattern_chunker.chunk_document(doc)
    
    assert len(pattern_chunks) > 0
    
    # Get statistics
    stats = pattern_chunker.get_pattern_statistics()
    assert isinstance(stats, dict)
    assert 'total' in stats


def test_drop_in_replacement():
    """Test that it can be used as a drop-in replacement for SemanticChunker."""
    content = """
# Test Document

## Section 1
Content here.

## Section 2
More content.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    config = ChunkerConfig(max_chunk_size=500)
    
    # Both should work with same interface
    regular_chunker = SemanticChunker.from_config(config)
    pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=False)
    
    regular_chunks = regular_chunker.chunk_document(doc)
    pattern_chunks = pattern_chunker.chunk_document(doc)
    
    # Should produce similar results when patterns disabled
    assert len(regular_chunks) == len(pattern_chunks)
    
    # Content should be the same
    for r_chunk, p_chunk in zip(regular_chunks, pattern_chunks):
        assert r_chunk.content == p_chunk.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
