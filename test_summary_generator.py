"""
Unit tests for SummaryGenerator.

Tests the summary generation functionality including LLM-based summaries
and fallback extractive summaries.
"""

import pytest
from src.user_manual_chunker.summary_generator import SummaryGenerator
from src.user_manual_chunker.data_models import (
    Section,
    Heading,
    Paragraph,
    CodeBlock,
    ChunkMetadata,
)
from src.user_manual_chunker.interfaces import DocumentChunk


class TestSummaryGenerator:
    """Test suite for SummaryGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SummaryGenerator(max_summary_length=50)
    
    def test_fallback_summary_with_code(self):
        """Test fallback summary generation for chunk with code."""
        # Create chunk with code
        heading = Heading(level=2, text="API Reference", line_number=1)
        paragraphs = [
            Paragraph(
                content="This function initializes the device and configures its parameters.",
                line_start=2,
                line_end=2
            )
        ]
        code_blocks = [
            CodeBlock(
                content="device.init()",
                language="python",
                line_start=4,
                line_end=4
            )
        ]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=code_blocks)
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=4
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["API Reference"],
            section_level=2,
            contains_code=True,
            code_languages=["python"],
            chunk_index=0,
            line_start=1,
            line_end=4,
            char_count=100
        )
        
        summary = self.generator._fallback_summary(chunk, metadata)
        
        # Verify summary mentions code
        assert "python" in summary.lower() or "code" in summary.lower() or "examples" in summary.lower()
        assert len(summary) > 0
    
    def test_fallback_summary_without_code(self):
        """Test fallback summary generation for chunk without code."""
        heading = Heading(level=1, text="Introduction", line_number=1)
        paragraphs = [
            Paragraph(
                content="This manual describes the device modeling language used for hardware simulation.",
                line_start=2,
                line_end=2
            )
        ]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=[])
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
            char_count=80
        )
        
        summary = self.generator._fallback_summary(chunk, metadata)
        
        # Verify summary is generated
        assert len(summary) > 0
        assert "Introduction" in summary or "manual" in summary.lower() or "device" in summary.lower()
    
    def test_fallback_summary_empty_content(self):
        """Test fallback summary with minimal content."""
        heading = Heading(level=3, text="Configuration", line_number=1)
        section = Section(heading=heading, paragraphs=[], code_blocks=[])
        chunk = DocumentChunk(
            content="### Configuration\n",
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=1
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Setup", "Configuration"],
            section_level=3,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=1,
            char_count=20
        )
        
        summary = self.generator._fallback_summary(chunk, metadata)
        
        # Should use heading-based fallback
        assert "Configuration" in summary
        assert len(summary) > 0
    
    def test_enforce_length_limit(self):
        """Test that summaries are truncated to max length."""
        long_summary = " ".join(["word"] * 100)  # 100 words
        
        truncated = self.generator._enforce_length_limit(long_summary)
        
        # Should be truncated to max_summary_length (50 words)
        word_count = len(truncated.split())
        assert word_count <= self.generator.max_summary_length + 1  # +1 for ellipsis
    
    def test_enforce_length_limit_short_text(self):
        """Test that short summaries are not modified."""
        short_summary = "This is a short summary."
        
        result = self.generator._enforce_length_limit(short_summary)
        
        assert result == short_summary
    
    def test_build_documentation_prompt_with_code(self):
        """Test prompt building for documentation with code."""
        heading = Heading(level=2, text="Examples", line_number=1)
        paragraphs = [Paragraph(content="Example usage:", line_start=2, line_end=2)]
        code_blocks = [CodeBlock(content="print('hello')", language="python", line_start=3, line_end=3)]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=code_blocks)
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=3
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Guide", "Examples"],
            section_level=2,
            contains_code=True,
            code_languages=["python"],
            chunk_index=0,
            line_start=1,
            line_end=3,
            char_count=50
        )
        
        prompt = self.generator._build_documentation_prompt(chunk, "Test Manual", metadata)
        
        # Verify prompt contains key elements
        assert "Test Manual" in prompt
        assert "Guide > Examples" in prompt
        assert "python" in prompt.lower()
        assert "code" in prompt.lower()
    
    def test_build_documentation_prompt_without_code(self):
        """Test prompt building for documentation without code."""
        heading = Heading(level=1, text="Overview", line_number=1)
        paragraphs = [Paragraph(content="This is an overview.", line_start=2, line_end=2)]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=[])
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=2
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Overview"],
            section_level=1,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=2,
            char_count=30
        )
        
        prompt = self.generator._build_documentation_prompt(chunk, "User Guide", metadata)
        
        # Verify prompt contains key elements
        assert "User Guide" in prompt
        assert "Overview" in prompt
        # Should not mention code
        assert "Contains Code: Yes" not in prompt
    
    def test_generate_summary_uses_fallback_on_error(self):
        """Test that generate_summary falls back on LLM error."""
        heading = Heading(level=2, text="Test Section", line_number=1)
        paragraphs = [
            Paragraph(
                content="This is a test paragraph with enough content to generate a summary.",
                line_start=2,
                line_end=2
            )
        ]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=[])
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=2
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Test Section"],
            section_level=2,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=2,
            char_count=70
        )
        
        # This will likely fail due to API issues, but should return fallback
        summary = self.generator.generate_summary(chunk, "Test Document", metadata)
        
        # Should get a valid summary (either LLM or fallback)
        assert len(summary) > 0
        assert isinstance(summary, str)
    
    def test_summary_length_constraint(self):
        """Test that generated summaries respect length constraints."""
        # Create a chunk with lots of content
        heading = Heading(level=2, text="Long Section", line_number=1)
        long_content = " ".join(["This is a sentence about the topic."] * 20)
        paragraphs = [Paragraph(content=long_content, line_start=2, line_end=2)]
        
        section = Section(heading=heading, paragraphs=paragraphs, code_blocks=[])
        chunk = DocumentChunk(
            content=section.get_text_content(),
            section=section,
            chunk_index=0,
            line_start=1,
            line_end=2
        )
        
        metadata = ChunkMetadata(
            source_file="test.md",
            heading_hierarchy=["Long Section"],
            section_level=2,
            contains_code=False,
            code_languages=[],
            chunk_index=0,
            line_start=1,
            line_end=2,
            char_count=len(long_content)
        )
        
        # Use a small max length
        small_generator = SummaryGenerator(max_summary_length=20)
        summary = small_generator.generate_summary(chunk, "Test Doc", metadata)
        
        # Verify length constraint
        word_count = len(summary.split())
        assert word_count <= 25  # Allow some buffer for ellipsis


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
