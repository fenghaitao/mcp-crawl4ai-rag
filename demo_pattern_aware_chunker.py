#!/usr/bin/env python3
"""
Demo script for PatternAwareSemanticChunker.

Shows how the pattern-aware chunker preserves special documentation
structures during chunking.
"""

from pathlib import Path
from src.user_manual_chunker import (
    PatternAwareSemanticChunker,
    SemanticChunkerImpl as SemanticChunker,
    MarkdownParser,
    ChunkerConfig,
)


def demo_comparison():
    """Compare regular chunker vs pattern-aware chunker."""
    print("=" * 80)
    print("Demo: Pattern-Aware Chunker vs Regular Chunker")
    print("=" * 80)
    
    # Sample document with API documentation pattern
    content = """
# Device API Reference

## Initialization Functions

### init()
Initialize the device with default settings. This function must be called
before any other device operations. It sets up internal state and prepares
the device for use.

```python
device.init()
```

### configure(mode, timeout=30)
Configure the device operation mode. The mode parameter determines how the
device processes requests. Available modes are 'sync' and 'async'.

Parameters:
- mode: Operation mode ('sync' or 'async')
- timeout: Maximum wait time in seconds

```python
device.configure(mode='async', timeout=60)
```

### reset()
Reset the device to factory defaults. This will clear all configuration
and return the device to its initial state.

```python
device.reset()
```

## Data Processing

### process_data(data)
Process input data through the device pipeline. The data is validated,
transformed, and then sent to the output buffer.

```python
result = device.process_data(input_data)
```

### get_status()
Retrieve current device status including operation mode, buffer levels,
and error state.

```python
status = device.get_status()
print(f"Mode: {status['mode']}")
print(f"Buffer: {status['buffer_level']}%")
```
"""
    
    # Parse document
    parser = MarkdownParser()
    doc = parser.parse(content, "api_reference.md")
    
    print(f"\nDocument structure:")
    print(f"  - Headings: {len(doc.headings)}")
    print(f"  - Paragraphs: {len(doc.paragraphs)}")
    print(f"  - Code blocks: {len(doc.code_blocks)}")
    print()
    
    # Create configuration with small chunk size to force splitting
    config = ChunkerConfig(
        max_chunk_size=400,  # Small size to demonstrate splitting
        min_chunk_size=100,
        chunk_overlap=0
    )
    
    # Test 1: Regular semantic chunker
    print("-" * 80)
    print("Test 1: Regular SemanticChunker")
    print("-" * 80)
    
    regular_chunker = SemanticChunker.from_config(config)
    regular_chunks = regular_chunker.chunk_document(doc)
    
    print(f"\nCreated {len(regular_chunks)} chunks\n")
    
    for i, chunk in enumerate(regular_chunks, 1):
        print(f"Chunk {i} ({len(chunk.content)} chars):")
        # Check if chunk splits API documentation
        has_function_sig = '###' in chunk.content or 'def ' in chunk.content or '()' in chunk.content
        has_code = '```' in chunk.content
        
        if has_function_sig and not has_code:
            print("  ⚠️  Contains function signature WITHOUT code example")
        elif has_code and not has_function_sig:
            print("  ⚠️  Contains code WITHOUT function signature")
        else:
            print("  ✓ Content appears complete")
        
        # Show first 100 chars
        preview = chunk.content.replace('\n', ' ')[:100]
        print(f"  Preview: {preview}...")
        print()
    
    # Test 2: Pattern-aware semantic chunker
    print("-" * 80)
    print("Test 2: PatternAwareSemanticChunker")
    print("-" * 80)
    
    pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    pattern_chunks = pattern_chunker.chunk_document(doc)
    
    print(f"\nCreated {len(pattern_chunks)} chunks\n")
    
    for i, chunk in enumerate(pattern_chunks, 1):
        print(f"Chunk {i} ({len(chunk.content)} chars):")
        # Check if chunk splits API documentation
        has_function_sig = '###' in chunk.content or 'def ' in chunk.content or '()' in chunk.content
        has_code = '```' in chunk.content
        
        if has_function_sig and not has_code:
            print("  ⚠️  Contains function signature WITHOUT code example")
        elif has_code and not has_function_sig:
            print("  ⚠️  Contains code WITHOUT function signature")
        else:
            print("  ✓ Content appears complete")
        
        # Show first 100 chars
        preview = chunk.content.replace('\n', ' ')[:100]
        print(f"  Preview: {preview}...")
        print()
    
    # Show pattern statistics
    print("-" * 80)
    print("Pattern Detection Statistics")
    print("-" * 80)
    
    # Re-run to get pattern stats
    pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    _ = pattern_chunker.chunk_document(doc)
    stats = pattern_chunker.get_pattern_statistics()
    
    print(f"\nDetected patterns:")
    print(f"  - Lists: {stats['lists']}")
    print(f"  - API documentation: {stats['api_docs']}")
    print(f"  - Grammar rules: {stats['grammar_rules']}")
    print(f"  - Definitions: {stats['definitions']}")
    print(f"  - Tables: {stats['tables']}")
    print(f"  - Cross-references: {stats['references']}")
    print(f"  - Total: {stats['total']}")
    print()
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\nRegular chunker: {len(regular_chunks)} chunks")
    print(f"Pattern-aware chunker: {len(pattern_chunks)} chunks")
    print()
    print("The pattern-aware chunker detects API documentation patterns")
    print("and keeps function signatures with their descriptions and code")
    print("examples, even if it means creating larger chunks.")


def demo_with_real_document():
    """Demo with a real Simics documentation file."""
    print("\n" + "=" * 80)
    print("Demo: Pattern-Aware Chunker with Real Documentation")
    print("=" * 80)
    
    # Find a sample document
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))
    
    if not sample_docs:
        print("\nNo sample documents found. Skipping demo.")
        return
    
    sample_doc = str(sample_docs[0])
    print(f"\nProcessing: {Path(sample_doc).name}")
    
    # Read content
    with open(sample_doc, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse document
    parser = MarkdownParser()
    doc = parser.parse(content, sample_doc)
    
    print(f"\nDocument structure:")
    print(f"  - Headings: {len(doc.headings)}")
    print(f"  - Paragraphs: {len(doc.paragraphs)}")
    print(f"  - Code blocks: {len(doc.code_blocks)}")
    
    # Create chunkers
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        chunk_overlap=50
    )
    
    regular_chunker = SemanticChunker.from_config(config)
    pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    
    # Chunk with both
    print("\nChunking with regular chunker...")
    regular_chunks = regular_chunker.chunk_document(doc)
    
    print("Chunking with pattern-aware chunker...")
    pattern_chunks = pattern_chunker.chunk_document(doc)
    
    # Get pattern statistics
    stats = pattern_chunker.get_pattern_statistics()
    
    print(f"\nResults:")
    print(f"  Regular chunker: {len(regular_chunks)} chunks")
    print(f"  Pattern-aware chunker: {len(pattern_chunks)} chunks")
    print(f"\nDetected patterns:")
    print(f"  - Lists: {stats['lists']}")
    print(f"  - API documentation: {stats['api_docs']}")
    print(f"  - Grammar rules: {stats['grammar_rules']}")
    print(f"  - Definitions: {stats['definitions']}")
    print(f"  - Tables: {stats['tables']}")
    print(f"  - Cross-references: {stats['references']}")
    print(f"  - Total: {stats['total']}")
    
    # Show first few chunks from pattern-aware chunker
    print(f"\nFirst 3 chunks from pattern-aware chunker:")
    for i, chunk in enumerate(pattern_chunks[:3], 1):
        print(f"\n  Chunk {i}:")
        print(f"    - Size: {len(chunk.content)} chars")
        print(f"    - Lines: {chunk.line_start}-{chunk.line_end}")
        print(f"    - Has code: {'```' in chunk.content}")
        preview = chunk.content.replace('\n', ' ')[:80]
        print(f"    - Preview: {preview}...")


def demo_enable_disable_patterns():
    """Demo enabling/disabling pattern detection."""
    print("\n" + "=" * 80)
    print("Demo: Enabling/Disabling Pattern Detection")
    print("=" * 80)
    
    content = """
# Grammar Rules

## Variable Declaration

Variables are declared using the `var` keyword:

```
var x: int = 42;
```

Example:
```
var name: string = "Alice";
var age: int = 30;
```

## Function Definition

Functions use the `function` keyword:

```
function add(a: int, b: int) -> int {
    return a + b;
}
```
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "grammar.md")
    
    config = ChunkerConfig(max_chunk_size=300, min_chunk_size=50, chunk_overlap=0)
    
    # Test with patterns enabled
    print("\n1. With pattern detection ENABLED:")
    chunker_enabled = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
    chunks_enabled = chunker_enabled.chunk_document(doc)
    print(f"   Created {len(chunks_enabled)} chunks")
    stats = chunker_enabled.get_pattern_statistics()
    print(f"   Detected {stats['grammar_rules']} grammar rules")
    
    # Test with patterns disabled
    print("\n2. With pattern detection DISABLED:")
    chunker_disabled = PatternAwareSemanticChunker.from_config(config, enable_patterns=False)
    chunks_disabled = chunker_disabled.chunk_document(doc)
    print(f"   Created {len(chunks_disabled)} chunks")
    stats = chunker_disabled.get_pattern_statistics()
    print(f"   Detected {stats['grammar_rules']} grammar rules (should be 0)")
    
    print("\nPattern detection can be toggled based on your needs:")
    print("  - Enable for technical documentation with special structures")
    print("  - Disable for simple documents or better performance")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("PatternAwareSemanticChunker Demo")
    print("=" * 80)
    
    # Demo 1: Comparison
    demo_comparison()
    
    # Demo 2: Real document
    demo_with_real_document()
    
    # Demo 3: Enable/disable
    demo_enable_disable_patterns()
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  ✓ PatternAwareSemanticChunker extends SemanticChunker")
    print("  ✓ Automatically detects special documentation patterns")
    print("  ✓ Keeps API docs, grammar rules, tables, etc. together")
    print("  ✓ Can be enabled/disabled as needed")
    print("  ✓ Drop-in replacement for SemanticChunker")


if __name__ == "__main__":
    main()
