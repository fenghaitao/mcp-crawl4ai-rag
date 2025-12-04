"""
Integration test for MetadataExtractor with real document parsing.

Tests the metadata extractor with actual markdown parsing and chunking.
"""

from src.user_manual_chunker import (
    MarkdownParser,
    SemanticChunkerImpl,
    MetadataExtractorImpl,
)


def test_metadata_with_real_markdown():
    """Test metadata extraction with real markdown document."""
    markdown_content = """# Device Modeling Language

The Device Modeling Language (DML) is a domain-specific language for modeling hardware devices.

## Basic Syntax

DML uses a C-like syntax with special keywords for device modeling.

```dml
device simple_device {
    bank regs {
        register r1 size 4 @ 0x00;
    }
}
```

### Register Definition

Registers are defined within banks using the `register` keyword.

```python
# Python example for comparison
class Register:
    def __init__(self, size):
        self.size = size
```

## Advanced Features

DML supports templates and methods for complex device behavior.
"""
    
    # Parse the document
    parser = MarkdownParser()
    doc_structure = parser.parse(markdown_content, source_path="/docs/dml_guide.md")
    
    # Chunk the document
    chunker = SemanticChunkerImpl(
        max_chunk_size=500,
        min_chunk_size=100,
        chunk_overlap=50
    )
    chunks = chunker.chunk_document(doc_structure)
    
    # Extract metadata for each chunk
    extractor = MetadataExtractorImpl()
    
    print(f"Document parsed into {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        metadata = extractor.extract(chunk, doc_structure)
        
        print(f"Chunk {i}:")
        print(f"  Source: {metadata.source_file}")
        print(f"  Hierarchy: {' > '.join(metadata.heading_hierarchy)}")
        print(f"  Section Level: {metadata.section_level}")
        print(f"  Contains Code: {metadata.contains_code}")
        print(f"  Languages: {metadata.code_languages}")
        print(f"  Lines: {metadata.line_start}-{metadata.line_end}")
        print(f"  Characters: {metadata.char_count}")
        print()
    
    # Verify expectations
    assert len(chunks) > 0, "Should have at least one chunk"
    
    # Check that at least one chunk has code
    has_code_chunk = any(
        extractor.extract(chunk, doc_structure).contains_code 
        for chunk in chunks
    )
    assert has_code_chunk, "At least one chunk should contain code"
    
    # Check that DML language is detected
    all_languages = set()
    for chunk in chunks:
        metadata = extractor.extract(chunk, doc_structure)
        all_languages.update(metadata.code_languages)
    
    assert "dml" in all_languages, "DML language should be detected"
    
    # Check heading hierarchy is built correctly
    metadata_first = extractor.extract(chunks[0], doc_structure)
    assert len(metadata_first.heading_hierarchy) > 0, "Should have heading hierarchy"
    assert metadata_first.source_file == "/docs/dml_guide.md", "Source file should be preserved"
    
    print("✅ Integration test passed!")


if __name__ == "__main__":
    print("Running MetadataExtractor integration test...\n")
    test_metadata_with_real_markdown()
