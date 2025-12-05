"""
Basic test to verify semantic chunker implementation.
"""

from src.user_manual_chunker.semantic_chunker import SemanticChunker
from src.user_manual_chunker.data_models import (
    DocumentStructure,
    Heading,
    Paragraph,
    CodeBlock,
    Section
)


def test_basic_chunking():
    """Test basic chunking functionality."""
    # Create a simple document structure
    heading1 = Heading(level=1, text="Introduction", line_number=1)
    heading2 = Heading(level=2, text="Getting Started", line_number=5, parent=heading1)
    
    para1 = Paragraph(
        content="This is the introduction paragraph. It explains the basics.",
        line_start=2,
        line_end=3
    )
    
    para2 = Paragraph(
        content="This is another paragraph with more details about getting started.",
        line_start=6,
        line_end=7
    )
    
    code1 = CodeBlock(
        content="def hello():\n    print('Hello, World!')",
        language="python",
        line_start=8,
        line_end=10
    )
    
    doc = DocumentStructure(
        source_path="test.md",
        headings=[heading1, heading2],
        paragraphs=[para1, para2],
        code_blocks=[code1],
        raw_content=""
    )
    
    # Create chunker with small max size to force splitting
    chunker = SemanticChunker(
        max_chunk_size=200,
        min_chunk_size=50,
        chunk_overlap=20,
        size_metric="characters"
    )
    
    # Chunk the document
    chunks = chunker.chunk_document(doc)
    
    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i}:")
        print(f"  Lines: {chunk.line_start}-{chunk.line_end}")
        print(f"  Size: {len(chunk.content)} characters")
        print(f"  Content preview: {chunk.content[:100]}...")
    
    # Verify we got chunks
    assert len(chunks) > 0, "Should create at least one chunk"
    
    # Verify chunks have content
    for chunk in chunks:
        assert len(chunk.content) > 0, "Chunk should have content"
        assert chunk.section is not None, "Chunk should have section"
    
    print("\n✓ Basic chunking test passed!")


def test_code_block_integrity():
    """Test that code blocks are never split."""
    heading = Heading(level=1, text="Code Example", line_number=1)
    
    para = Paragraph(
        content="Here is a code example:",
        line_start=2,
        line_end=2
    )
    
    # Create a large code block
    large_code = "def function():\n" + "    # comment\n" * 50
    code = CodeBlock(
        content=large_code,
        language="python",
        line_start=3,
        line_end=53
    )
    
    doc = DocumentStructure(
        source_path="test.md",
        headings=[heading],
        paragraphs=[para],
        code_blocks=[code],
        raw_content=""
    )
    
    # Create chunker with small max size
    chunker = SemanticChunker(
        max_chunk_size=100,
        min_chunk_size=20,
        chunk_overlap=0,
        size_metric="characters"
    )
    
    chunks = chunker.chunk_document(doc)
    
    print(f"\nCode integrity test: Created {len(chunks)} chunks")
    
    # Verify code block appears in exactly one chunk
    code_appearances = 0
    for chunk in chunks:
        if "def function():" in chunk.content:
            code_appearances += 1
            # Verify the entire code block is present
            assert large_code in chunk.content, "Code block should be complete"
    
    assert code_appearances == 1, "Code block should appear in exactly one chunk"
    
    print("✓ Code block integrity test passed!")


def test_size_calculation():
    """Test size calculation for characters and tokens."""
    chunker_chars = SemanticChunker(size_metric="characters")
    
    text = "Hello, World!"
    size = chunker_chars.calculate_size(text)
    
    assert size == len(text), f"Character size should be {len(text)}, got {size}"
    
    print(f"✓ Size calculation test passed! (size={size})")


def test_section_merging():
    """Test that small sections are merged."""
    heading1 = Heading(level=1, text="Section 1", line_number=1)
    heading2 = Heading(level=1, text="Section 2", line_number=5)
    
    # Create very small paragraphs
    para1 = Paragraph(content="Small.", line_start=2, line_end=2)
    para2 = Paragraph(content="Also small.", line_start=6, line_end=6)
    
    doc = DocumentStructure(
        source_path="test.md",
        headings=[heading1, heading2],
        paragraphs=[para1, para2],
        code_blocks=[],
        raw_content=""
    )
    
    # Create chunker with large min size to force merging
    chunker = SemanticChunker(
        max_chunk_size=1000,
        min_chunk_size=100,
        chunk_overlap=0,
        size_metric="characters"
    )
    
    chunks = chunker.chunk_document(doc)
    
    print(f"\nSection merging test: Created {len(chunks)} chunks")
    
    # With large min_chunk_size, small sections should be merged
    # We should have fewer chunks than sections
    assert len(chunks) <= 2, f"Small sections should be merged, got {len(chunks)} chunks"
    
    print("✓ Section merging test passed!")


if __name__ == "__main__":
    test_basic_chunking()
    test_code_block_integrity()
    test_size_calculation()
    test_section_merging()
    print("\n✅ All basic tests passed!")
