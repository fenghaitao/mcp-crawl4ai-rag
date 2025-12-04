"""
Tests for MetadataExtractor implementation.

Validates metadata extraction including heading hierarchy, code language detection,
and document provenance.
"""

import pytest
from src.user_manual_chunker import (
    MetadataExtractorImpl,
    DocumentStructure,
    Heading,
    CodeBlock,
    Paragraph,
    Section,
    DocumentChunk,
)


def test_metadata_extractor_basic():
    """Test basic metadata extraction."""
    # Create a simple document structure
    h1 = Heading(level=1, text="Introduction", line_number=1)
    h2 = Heading(level=2, text="Getting Started", line_number=5, parent=h1)
    
    code_block = CodeBlock(
        content="def hello():\n    print('Hello')",
        language="python",
        line_start=10,
        line_end=12
    )
    
    paragraph = Paragraph(
        content="This is a test paragraph.",
        line_start=7,
        line_end=8
    )
    
    doc_structure = DocumentStructure(
        source_path="/path/to/document.md",
        headings=[h1, h2],
        paragraphs=[paragraph],
        code_blocks=[code_block],
        raw_content="# Introduction\n\n## Getting Started\n\nThis is a test paragraph.\n\n```python\ndef hello():\n    print('Hello')\n```"
    )
    
    # Create a section and chunk
    section = Section(
        heading=h2,
        paragraphs=[paragraph],
        code_blocks=[code_block]
    )
    
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=5,
        line_end=12
    )
    
    # Extract metadata
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    # Verify metadata
    assert metadata.source_file == "/path/to/document.md"
    assert metadata.heading_hierarchy == ["Introduction", "Getting Started"]
    assert metadata.section_level == 2
    assert metadata.contains_code is True
    assert "python" in metadata.code_languages
    assert metadata.chunk_index == 0
    assert metadata.line_start == 5
    assert metadata.line_end == 12
    assert metadata.char_count > 0
    
    print("✓ Basic metadata extraction test passed")


def test_heading_hierarchy_extraction():
    """Test heading hierarchy building."""
    # Create nested heading structure
    h1 = Heading(level=1, text="Chapter 1", line_number=1)
    h2 = Heading(level=2, text="Section 1.1", line_number=5, parent=h1)
    h3 = Heading(level=3, text="Subsection 1.1.1", line_number=10, parent=h2)
    
    doc_structure = DocumentStructure(
        source_path="/path/to/doc.md",
        headings=[h1, h2, h3],
        paragraphs=[],
        code_blocks=[]
    )
    
    section = Section(heading=h3, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="### Subsection 1.1.1\n",
        section=section,
        chunk_index=0,
        line_start=10,
        line_end=10
    )
    
    extractor = MetadataExtractorImpl()
    hierarchy = extractor.build_heading_hierarchy(chunk)
    
    assert hierarchy == ["Chapter 1", "Section 1.1", "Subsection 1.1.1"]
    assert len(hierarchy) == 3
    
    print("✓ Heading hierarchy extraction test passed")


def test_code_language_detection_explicit():
    """Test code language detection with explicit language."""
    code_block = CodeBlock(
        content="function test() { return 42; }",
        language="javascript",
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(code_block)
    
    assert language == "javascript"
    
    print("✓ Explicit code language detection test passed")


def test_code_language_detection_heuristic():
    """Test code language detection using heuristics."""
    # Python code
    python_code = CodeBlock(
        content="def hello():\n    print('Hello, World!')\n    import sys",
        language="",
        line_start=1,
        line_end=3
    )
    
    extractor = MetadataExtractorImpl()
    language = extractor.detect_code_language(python_code)
    
    assert language == "python"
    
    # DML code
    dml_code = CodeBlock(
        content="device simple_device {\n    bank regs {\n        register r1 size 4;\n    }\n}",
        language="",
        line_start=1,
        line_end=5
    )
    
    language = extractor.detect_code_language(dml_code)
    assert language == "dml"
    
    print("✓ Heuristic code language detection test passed")


def test_no_code_metadata():
    """Test metadata extraction for chunks without code."""
    h1 = Heading(level=1, text="Introduction", line_number=1)
    
    paragraph = Paragraph(
        content="This is a paragraph without code.",
        line_start=3,
        line_end=4
    )
    
    doc_structure = DocumentStructure(
        source_path="/path/to/doc.md",
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
        line_end=4
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.contains_code is False
    assert len(metadata.code_languages) == 0
    
    print("✓ No code metadata test passed")


def test_multiple_code_languages():
    """Test metadata extraction with multiple code languages."""
    h1 = Heading(level=1, text="Examples", line_number=1)
    
    python_code = CodeBlock(
        content="print('Hello')",
        language="python",
        line_start=5,
        line_end=5
    )
    
    js_code = CodeBlock(
        content="console.log('Hello')",
        language="javascript",
        line_start=10,
        line_end=10
    )
    
    doc_structure = DocumentStructure(
        source_path="/path/to/doc.md",
        headings=[h1],
        paragraphs=[],
        code_blocks=[python_code, js_code]
    )
    
    section = Section(heading=h1, paragraphs=[], code_blocks=[python_code, js_code])
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=10
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.contains_code is True
    assert len(metadata.code_languages) == 2
    assert "python" in metadata.code_languages
    assert "javascript" in metadata.code_languages
    
    print("✓ Multiple code languages test passed")


def test_section_level_calculation():
    """Test section level calculation."""
    # Test different hierarchy depths
    h1 = Heading(level=1, text="Level 1", line_number=1)
    
    doc_structure = DocumentStructure(
        source_path="/path/to/doc.md",
        headings=[h1],
        paragraphs=[],
        code_blocks=[]
    )
    
    section = Section(heading=h1, paragraphs=[], code_blocks=[])
    chunk = DocumentChunk(
        content="# Level 1\n",
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=1
    )
    
    extractor = MetadataExtractorImpl()
    metadata = extractor.extract(chunk, doc_structure)
    
    assert metadata.section_level == 1
    
    # Test nested hierarchy
    h2 = Heading(level=2, text="Level 2", line_number=5, parent=h1)
    h3 = Heading(level=3, text="Level 3", line_number=10, parent=h2)
    
    section3 = Section(heading=h3, paragraphs=[], code_blocks=[])
    chunk3 = DocumentChunk(
        content="### Level 3\n",
        section=section3,
        chunk_index=1,
        line_start=10,
        line_end=10
    )
    
    metadata3 = extractor.extract(chunk3, doc_structure)
    assert metadata3.section_level == 3
    
    print("✓ Section level calculation test passed")


def test_extract_all_code_languages():
    """Test extracting all languages from a document."""
    python_code = CodeBlock(
        content="print('test')",
        language="python",
        line_start=1,
        line_end=1
    )
    
    dml_code = CodeBlock(
        content="device test {}",
        language="dml",
        line_start=5,
        line_end=5
    )
    
    doc_structure = DocumentStructure(
        source_path="/path/to/doc.md",
        headings=[],
        paragraphs=[],
        code_blocks=[python_code, dml_code]
    )
    
    extractor = MetadataExtractorImpl()
    languages = extractor.extract_all_code_languages(doc_structure)
    
    assert "python" in languages
    assert "dml" in languages
    assert len(languages) == 2
    
    print("✓ Extract all code languages test passed")


if __name__ == "__main__":
    print("Running MetadataExtractor tests...\n")
    
    test_metadata_extractor_basic()
    test_heading_hierarchy_extraction()
    test_code_language_detection_explicit()
    test_code_language_detection_heuristic()
    test_no_code_metadata()
    test_multiple_code_languages()
    test_section_level_calculation()
    test_extract_all_code_languages()
    
    print("\n✅ All MetadataExtractor tests passed!")
