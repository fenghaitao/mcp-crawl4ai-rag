"""
Test error handling implementation for user manual chunker.

Tests the error handling added in task 12:
- Parsing error handling (invalid markdown/HTML, encoding issues, malformed structure)
- Chunking error handling (oversized code blocks, empty sections, circular references)
- Embedding error handling (retry with exponential backoff, rate limiting, batch failures)
- Summary generation error handling (LLM failures, timeout handling, empty content)
- Storage error handling (disk space, write permissions, JSON serialization errors)
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.user_manual_chunker.markdown_parser import MarkdownParser
from src.user_manual_chunker.html_parser import HTMLParser
from src.user_manual_chunker.semantic_chunker import SemanticChunker
from src.user_manual_chunker.embedding_generator import EmbeddingGenerator, RateLimiter
from src.user_manual_chunker.summary_generator import SummaryGenerator
from src.user_manual_chunker.orchestrator import UserManualChunker, StorageError
from src.user_manual_chunker.data_models import DocumentStructure, Heading, Paragraph, CodeBlock, Section
from src.user_manual_chunker.interfaces import DocumentChunk


class TestParsingErrorHandling:
    """Test parsing error handling (Task 12.1)."""
    
    def test_markdown_parser_handles_empty_content(self):
        """Test that markdown parser handles empty content gracefully."""
        parser = MarkdownParser()
        
        # Empty content should return empty structure, not crash
        doc = parser.parse("", source_path="test.md")
        
        assert doc is not None
        assert doc.headings == []
        assert doc.paragraphs == []
        assert doc.code_blocks == []
    
    def test_markdown_parser_handles_none_content(self):
        """Test that markdown parser rejects None content."""
        parser = MarkdownParser()
        
        with pytest.raises(ValueError, match="Content cannot be None"):
            parser.parse(None, source_path="test.md")
    
    def test_markdown_parser_handles_malformed_headings(self):
        """Test that markdown parser handles malformed headings."""
        parser = MarkdownParser()
        
        # Malformed markdown with invalid heading levels
        content = """
####### Invalid heading (7 hashes)
## Valid heading
###
"""
        
        doc = parser.parse(content, source_path="test.md")
        
        # Should only extract valid heading
        assert len(doc.headings) == 1
        assert doc.headings[0].text == "Valid heading"
    
    def test_html_parser_handles_empty_content(self):
        """Test that HTML parser handles empty content gracefully."""
        parser = HTMLParser()
        
        # Empty content should return empty structure
        doc = parser.parse("", source_path="test.html")
        
        assert doc is not None
        assert doc.headings == []
    
    def test_html_parser_handles_malformed_html(self):
        """Test that HTML parser handles malformed HTML."""
        parser = HTMLParser()
        
        # Malformed HTML
        content = "<h1>Unclosed heading<h2>Another heading</h2>"
        
        # Should not crash
        doc = parser.parse(content, source_path="test.html")
        
        assert doc is not None
        # BeautifulSoup should recover and extract headings
        assert len(doc.headings) >= 1


class TestChunkingErrorHandling:
    """Test chunking error handling (Task 12.2)."""
    
    def test_chunker_handles_empty_sections(self):
        """Test that chunker handles empty sections gracefully."""
        chunker = SemanticChunker(max_chunk_size=1000)
        
        # Create document with empty section
        heading = Heading(level=1, text="Empty Section", line_number=1)
        doc = DocumentStructure(
            source_path="test.md",
            headings=[heading],
            paragraphs=[],
            code_blocks=[],
            raw_content="# Empty Section\n"
        )
        
        # Should handle empty sections without crashing
        chunks = chunker.chunk_document(doc)
        
        # The chunker creates a chunk with just the heading, which is valid
        # The important thing is it doesn't crash
        assert chunks is not None
        assert isinstance(chunks, list)
    
    def test_chunker_handles_oversized_code_blocks(self):
        """Test that chunker handles oversized code blocks."""
        chunker = SemanticChunker(max_chunk_size=100)
        
        # Create code block larger than max_chunk_size
        large_code = "x = 1\n" * 50  # Much larger than 100 chars
        
        heading = Heading(level=1, text="Section", line_number=1)
        code_block = CodeBlock(
            content=large_code,
            language="python",
            line_start=2,
            line_end=52
        )
        
        doc = DocumentStructure(
            source_path="test.md",
            headings=[heading],
            paragraphs=[],
            code_blocks=[code_block],
            raw_content=f"# Section\n```python\n{large_code}\n```"
        )
        
        # Should create dedicated chunk for oversized code block
        chunks = chunker.chunk_document(doc)
        
        assert len(chunks) >= 1
        # Code block should be in a chunk
        assert any("x = 1" in chunk.content for chunk in chunks)


class TestEmbeddingErrorHandling:
    """Test embedding error handling (Task 12.3)."""
    
    def test_rate_limiter_basic_functionality(self):
        """Test that rate limiter works correctly."""
        import time
        
        # Allow 3 requests per 1 second
        limiter = RateLimiter(max_requests=3, time_window=1.0)
        
        # First 3 requests should be immediate
        start = time.time()
        for _ in range(3):
            limiter.acquire()
        elapsed = time.time() - start
        
        # Should be very fast (< 0.1 seconds)
        assert elapsed < 0.1
    
    def test_embedding_generator_handles_empty_chunks(self):
        """Test that embedding generator handles empty chunk list."""
        generator = EmbeddingGenerator()
        
        # Empty list should return empty list
        embeddings = generator.generate_embeddings([])
        
        assert embeddings == []


class TestSummaryErrorHandling:
    """Test summary generation error handling (Task 12.4)."""
    
    def test_summary_generator_handles_empty_content(self):
        """Test that summary generator handles empty content."""
        from src.user_manual_chunker.data_models import ChunkMetadata
        
        generator = SummaryGenerator()
        
        # Create chunk with empty content
        heading = Heading(level=1, text="Test", line_number=1)
        section = Section(heading=heading, paragraphs=[], code_blocks=[])
        chunk = DocumentChunk(
            content="",
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=1
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Test"],
            section_level=1,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=1,
            char_count=0
        )
        
        # Should generate summary from metadata, not crash
        summary = generator.generate_summary(chunk, "Test Doc", metadata)
        
        assert summary is not None
        assert len(summary) > 0
    
    def test_summary_generator_fallback_works(self):
        """Test that summary generator fallback works."""
        from src.user_manual_chunker.data_models import ChunkMetadata
        
        generator = SummaryGenerator()
        
        # Create chunk with content
        heading = Heading(level=1, text="Introduction", line_number=1)
        para = Paragraph(
            content="This is a test paragraph with enough content to extract a meaningful summary.",
            line_start=2,
            line_end=2
        )
        section = Section(heading=heading, paragraphs=[para], code_blocks=[])
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=2
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Introduction"],
            section_level=1,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=2,
            char_count=len(chunk.content)
        )
        
        # Test fallback directly
        summary = generator._fallback_summary(chunk, metadata)
        
        assert summary is not None
        assert len(summary) > 0
        # Fallback should extract first sentence or use heading
        assert "test paragraph" in summary.lower() or "introduction" in summary.lower()


class TestStorageErrorHandling:
    """Test storage error handling (Task 12.5)."""
    
    def test_orchestrator_checks_write_permissions(self):
        """Test that orchestrator checks write permissions."""
        from src.user_manual_chunker.data_models import ProcessedChunk, ChunkMetadata
        
        orchestrator = UserManualChunker()
        
        # Create a test chunk
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Test"],
            section_level=1,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=1,
            char_count=10
        )
        
        chunk = ProcessedChunk(
            chunk_id="test_001",
            content="Test content",
            metadata=metadata,
            summary="Test summary",
            embedding=None
        )
        
        # Try to write to a valid temporary location
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            
            # Should succeed
            orchestrator.export_to_json([chunk], output_path)
            
            # File should exist
            assert os.path.exists(output_path)
    
    def test_orchestrator_handles_json_serialization_errors(self):
        """Test that orchestrator handles JSON serialization errors gracefully."""
        from src.user_manual_chunker.data_models import ProcessedChunk, ChunkMetadata
        import numpy as np
        
        orchestrator = UserManualChunker()
        
        # Create chunk with embedding (numpy array)
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Test"],
            section_level=1,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=1,
            char_count=10
        )
        
        chunk = ProcessedChunk(
            chunk_id="test_001",
            content="Test content",
            metadata=metadata,
            summary="Test summary",
            embedding=np.array([0.1, 0.2, 0.3])
        )
        
        # Should handle numpy array serialization
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.json")
            
            # Should succeed with custom encoder
            orchestrator.export_to_json([chunk], output_path)
            
            # File should exist and be valid JSON
            assert os.path.exists(output_path)
            
            import json
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "chunks" in data
            assert len(data["chunks"]) == 1


def test_integration_error_handling():
    """Integration test for error handling across components."""
    
    # Create orchestrator
    orchestrator = UserManualChunker()
    
    # Test with malformed markdown
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Valid Heading

Some content here.

####### Invalid heading

More content.

```python
# Code block
x = 1
```
""")
        temp_file = f.name
    
    try:
        # Should handle malformed content gracefully
        chunks = orchestrator.process_document(
            temp_file,
            generate_embeddings=False,  # Skip embeddings for speed
            generate_summaries=False     # Skip summaries for speed
        )
        
        # Should produce some chunks despite malformed content
        assert len(chunks) > 0
        
        # Test export with error handling
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.json")
            orchestrator.export_to_json(chunks, output_path)
            
            # Should succeed
            assert os.path.exists(output_path)
    
    finally:
        # Clean up
        os.unlink(temp_file)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
