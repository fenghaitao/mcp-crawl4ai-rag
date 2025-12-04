"""
Edge case tests for MetadataExtractor.

Tests various edge cases and boundary conditions.
"""

from src.user_manual_chunker import (
    MetadataExtractorImpl,
    DocumentStructure,
    Heading,
    CodeBlock,
    Paragraph,
    Section,
    DocumentChunk,
)


def test_empty_document():
    """Test metadata extraction from empty document."""
    doc_structure = DocumentStructure(
        source_path="/empty.md",
        headings=[],
        paragraphs=[],
        code_blocks=[]
    )
    
    # Create a minimal chunk
    dummy_heading = Heading(level=1, text="Empty", line_number=1)
    section = Section(heading=dummy_heading, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="# Empty\n",
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.source_file == "/empty.md"
    assert metadata.contains_code is False
    assert len(metadata.code_languages) == 0
    
    print("✓ Empty document test passed")


def test_unknown_language_detection():
    """Test code block with unknown language."""
    code_block = CodeBlock(
        content="some random text that doesn't match any language",
        language="",
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(code_block)
    
    assert language == "unknown"
    
    print("✓ Unknown language detection test passed")


def test_flat_hierarchy():
    """Test document with only top-level headings (no nesting)."""
    h1 = Heading(level=1, text="Section 1", line_number=1)
    h2 = Heading(level=1, text="Section 2", line_number=10)
    
    doc_structure = DocumentStructure(
        source_path="/flat.md",
        headings=[h1, h2],
        paragraphs=[],
        code_blocks=[]
    )
    
    section = Section(heading=h1, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="# Section 1\n",
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.heading_hierarchy == ["Section 1"]
    assert metadata.section_level == 1
    
    print("✓ Flat hierarchy test passed")


def test_deep_hierarchy():
    """Test document with deep heading nesting."""
    h1 = Heading(level=1, text="L1", line_number=1)
    h2 = Heading(level=2, text="L2", line_number=5, parent=h1)
    h3 = Heading(level=3, text="L3", line_number=10, parent=h2)
    h4 = Heading(level=4, text="L4", line_number=15, parent=h3)
    h5 = Heading(level=5, text="L5", line_number=20, parent=h4)
    h6 = Heading(level=6, text="L6", line_number=25, parent=h5)
    
    doc_structure = DocumentStructure(
        source_path="/deep.md",
        headings=[h1, h2, h3, h4, h5, h6],
        paragraphs=[],
        code_blocks=[]
    )
    
    section = Section(heading=h6, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="###### L6\n",
        section=section,
        chunk_index=0,
        line_start=25,
        line_end=25
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.heading_hierarchy == ["L1", "L2", "L3", "L4", "L5", "L6"]
    assert metadata.section_level == 6
    
    print("✓ Deep hierarchy test passed")


def test_mixed_case_language():
    """Test language detection with mixed case."""
    code_block = CodeBlock(
        content="def test(): pass",
        language="Python",  # Mixed case
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(code_block)
    
    assert language == "python"  # Should be normalized to lowercase
    
    print("✓ Mixed case language test passed")


def test_whitespace_language():
    """Test code block with whitespace-only language."""
    code_block = CodeBlock(
        content="def test(): pass",
        language="   ",  # Whitespace only
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(code_block)
    
    # Should fall back to heuristic detection
    assert language == "python"
    
    print("✓ Whitespace language test passed")


def test_duplicate_languages():
    """Test that duplicate languages are not added twice."""
    h1 = Heading(level=1, text="Test", line_number=1)
    
    code1 = CodeBlock(
        content="print('hello')",
        language="python",
        line_start=5,
        line_end=5
    )
    
    code2 = CodeBlock(
        content="print('world')",
        language="python",
        line_start=10,
        line_end=10
    )
    
    doc_structure = DocumentStructure(
        source_path="/test.md",
        headings=[h1],
        paragraphs=[],
        code_blocks=[code1, code2]
    )
    
    section = Section(heading=h1, paragraphs=[], code_blocks=[code1, code2])
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=10
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert len(metadata.code_languages) == 1
    assert metadata.code_languages[0] == "python"
    
    print("✓ Duplicate languages test passed")


def test_special_characters_in_heading():
    """Test heading with special characters."""
    h1 = Heading(level=1, text="C++ & Rust: A Comparison", line_number=1)
    
    doc_structure = DocumentStructure(
        source_path="/test.md",
        headings=[h1],
        paragraphs=[],
        code_blocks=[]
    )
    
    section = Section(heading=h1, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="# C++ & Rust: A Comparison\n",
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.heading_hierarchy == ["C++ & Rust: A Comparison"]
    
    print("✓ Special characters in heading test passed")


def test_very_long_content():
    """Test metadata extraction with very long content."""
    h1 = Heading(level=1, text="Long Content", line_number=1)
    
    # Create a very long paragraph
    long_text = "This is a test. " * 1000  # 16000 characters
    paragraph = Paragraph(
        content=long_text,
        line_start=3,
        line_end=100
    )
    
    doc_structure = DocumentStructure(
        source_path="/long.md",
        headings=[h1],
        paragraphs=[paragraph],
        code_blocks=[]
    )
    
    section = Section(heading=h1, paragraphs=[paragraph], code_blocks=[])
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=100
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.char_count > 16000
    assert metadata.line_start == 1
    assert metadata.line_end == 100
    
    print("✓ Very long content test passed")


def test_c_language_detection():
    """Test C language detection with various patterns."""
    c_code = CodeBlock(
        content="""
#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    return 0;
}
""",
        language="",
        line_start=1,
        line_end=7
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(c_code)
    
    assert language == "c"
    
    print("✓ C language detection test passed")


def test_shell_script_detection():
    """Test shell script detection."""
    shell_code = CodeBlock(
        content="""#!/bin/bash
echo "Starting process..."
export PATH=/usr/local/bin:$PATH
if [ -f config.txt ]; then
    echo "Config found"
fi
""",
        language="",
        line_start=1,
        line_end=6
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(shell_code)
    
    assert language == "shell"
    
    print("✓ Shell script detection test passed")


if __name__ == "__main__":
    print("Running MetadataExtractor edge case tests...\n")
    
    test_empty_document()
    test_unknown_language_detection()
    test_flat_hierarchy()
    test_deep_hierarchy()
    test_mixed_case_language()
    test_whitespace_language()
    test_duplicate_languages()
    test_special_characters_in_heading()
    test_very_long_content()
    test_c_language_detection()
    test_shell_script_detection()
    
    print("\n✅ All edge case tests passed!")
