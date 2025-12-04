"""
Demo script for MetadataExtractor functionality.

Demonstrates metadata extraction from a sample technical document.
"""

from src.user_manual_chunker import (
    MarkdownParser,
    SemanticChunkerImpl,
    MetadataExtractorImpl,
)


def main():
    """Demonstrate metadata extraction capabilities."""
    
    # Sample technical documentation
    sample_doc = """# Simics Device Modeling Language (DML) Guide

DML is a domain-specific language designed for modeling hardware devices in the Simics simulator.

## Introduction to DML

DML provides a high-level abstraction for device modeling, making it easier to create accurate hardware models.

### Key Features

- Object-oriented design with templates
- Built-in support for registers and banks
- Automatic generation of device interfaces

## Basic Device Structure

A simple device in DML consists of banks and registers:

```dml
device simple_uart {
    bank regs {
        register data size 1 @ 0x00 {
            method write(uint8 value) {
                // Handle data write
            }
        }
        
        register status size 1 @ 0x01 is read_only;
    }
}
```

### Register Operations

Registers support read and write operations through methods:

```python
# Python equivalent for comparison
class Register:
    def __init__(self, size, offset):
        self.size = size
        self.offset = offset
    
    def write(self, value):
        # Handle write operation
        pass
```

## Advanced Topics

### Templates

Templates allow code reuse across multiple devices:

```dml
template register_with_logging {
    method write(uint64 value) {
        log info: "Writing %d to register", value;
        default(value);
    }
}
```

### Event Handling

DML supports event-driven programming for device behavior.
"""
    
    print("=" * 70)
    print("MetadataExtractor Demo")
    print("=" * 70)
    print()
    
    # Parse the document
    print("📄 Parsing markdown document...")
    parser = MarkdownParser()
    doc_structure = parser.parse(sample_doc, source_path="/docs/dml_guide.md")
    print(f"   Found {len(doc_structure.headings)} headings")
    print(f"   Found {len(doc_structure.code_blocks)} code blocks")
    print(f"   Found {len(doc_structure.paragraphs)} paragraphs")
    print()
    
    # Chunk the document
    print("✂️  Chunking document...")
    chunker = SemanticChunkerImpl(
        max_chunk_size=800,
        min_chunk_size=100,
        chunk_overlap=50
    )
    chunks = chunker.chunk_document(doc_structure)
    print(f"   Created {len(chunks)} chunks")
    print()
    
    # Extract metadata
    print("🔍 Extracting metadata from chunks...")
    print()
    extractor = MetadataExtractorImpl()
    
    for i, chunk in enumerate(chunks):
        metadata = extractor.extract(chunk, doc_structure)
        
        print(f"📦 Chunk {i + 1}/{len(chunks)}")
        print(f"   {'─' * 60}")
        print(f"   📁 Source: {metadata.source_file}")
        print(f"   📊 Hierarchy: {' → '.join(metadata.heading_hierarchy)}")
        print(f"   📏 Section Level: {metadata.section_level}")
        print(f"   💻 Contains Code: {'Yes' if metadata.contains_code else 'No'}")
        
        if metadata.code_languages:
            print(f"   🔤 Languages: {', '.join(metadata.code_languages)}")
        
        print(f"   📍 Lines: {metadata.line_start}-{metadata.line_end}")
        print(f"   📝 Characters: {metadata.char_count}")
        print(f"   🔢 Chunk Index: {metadata.chunk_index}")
        print()
    
    # Summary statistics
    print("=" * 70)
    print("📊 Summary Statistics")
    print("=" * 70)
    
    total_chars = sum(
        extractor.extract(chunk, doc_structure).char_count 
        for chunk in chunks
    )
    
    chunks_with_code = sum(
        1 for chunk in chunks 
        if extractor.extract(chunk, doc_structure).contains_code
    )
    
    all_languages = set()
    for chunk in chunks:
        metadata = extractor.extract(chunk, doc_structure)
        all_languages.update(metadata.code_languages)
    
    max_hierarchy_depth = max(
        extractor.extract(chunk, doc_structure).section_level 
        for chunk in chunks
    )
    
    print(f"Total chunks: {len(chunks)}")
    print(f"Total characters: {total_chars}")
    print(f"Average chunk size: {total_chars // len(chunks)} characters")
    print(f"Chunks with code: {chunks_with_code} ({chunks_with_code * 100 // len(chunks)}%)")
    print(f"Languages detected: {', '.join(sorted(all_languages))}")
    print(f"Maximum hierarchy depth: {max_hierarchy_depth}")
    print()
    
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
