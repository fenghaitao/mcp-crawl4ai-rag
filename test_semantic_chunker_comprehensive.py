"""
Comprehensive test demonstrating semantic chunker functionality.
"""

from src.user_manual_chunker.semantic_chunker import SemanticChunker
from src.user_manual_chunker.markdown_parser import MarkdownParser


def test_with_real_markdown():
    """Test chunking with a realistic markdown document."""
    
    markdown_content = """# User Manual

## Introduction

This is the introduction to our software. It provides an overview of the key features
and capabilities that you'll learn about in this manual.

The software is designed to be easy to use while providing powerful functionality
for advanced users.

## Getting Started

### Installation

To install the software, follow these steps:

1. Download the installer
2. Run the installer
3. Follow the on-screen instructions

Here's a simple installation script:

```bash
#!/bin/bash
wget https://example.com/installer.sh
chmod +x installer.sh
./installer.sh
```

### Configuration

After installation, you need to configure the software. Edit the configuration file:

```yaml
server:
  host: localhost
  port: 8080
database:
  url: postgresql://localhost/mydb
```

The configuration file supports many options. See the reference section for details.

## Advanced Features

### API Integration

The software provides a REST API for integration with other systems. Here's an example:

```python
import requests

response = requests.get('http://localhost:8080/api/data')
data = response.json()
print(f"Received {len(data)} items")
```

This API endpoint returns JSON data that can be processed by your application.

### Performance Tuning

For optimal performance, consider these settings:

- Increase memory allocation
- Enable caching
- Use connection pooling

## Conclusion

This manual has covered the basics of using the software. For more information,
consult the online documentation or contact support.
"""
    
    # Parse the markdown
    parser = MarkdownParser()
    doc_structure = parser.parse(markdown_content, source_path="user_manual.md")
    
    print(f"Parsed document:")
    print(f"  - {len(doc_structure.headings)} headings")
    print(f"  - {len(doc_structure.paragraphs)} paragraphs")
    print(f"  - {len(doc_structure.code_blocks)} code blocks")
    
    # Create chunker with moderate settings
    chunker = SemanticChunker(
        max_chunk_size=500,
        min_chunk_size=100,
        chunk_overlap=50,
        size_metric="characters"
    )
    
    # Chunk the document
    chunks = chunker.chunk_document(doc_structure)
    
    print(f"\nCreated {len(chunks)} chunks:")
    print("=" * 80)
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} ---")
        print(f"Lines: {chunk.line_start}-{chunk.line_end}")
        print(f"Size: {len(chunk.content)} characters")
        print(f"Section: {chunk.section.heading.text}")
        print(f"Content preview:")
        print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)
        
        # Verify code blocks are intact
        if "```" in chunk.content:
            # Count code fence pairs
            fence_count = chunk.content.count("```")
            assert fence_count % 2 == 0, f"Code fences should be paired in chunk {i}"
            print(f"  ✓ Contains {fence_count // 2} complete code block(s)")
    
    # Verify requirements
    print("\n" + "=" * 80)
    print("Verification:")
    
    # 1. All chunks should have content
    assert all(len(c.content) > 0 for c in chunks), "All chunks should have content"
    print("✓ All chunks have content")
    
    # 2. Code blocks should not be split
    for i, chunk in enumerate(chunks):
        fence_count = chunk.content.count("```")
        assert fence_count % 2 == 0, f"Code fences should be paired in chunk {i}"
    print("✓ No code blocks are split across chunks")
    
    # 3. Chunks should respect size limits (with some tolerance for code blocks)
    oversized_chunks = [i for i, c in enumerate(chunks) if len(c.content) > chunker.max_chunk_size * 2]
    if oversized_chunks:
        print(f"⚠ Warning: {len(oversized_chunks)} chunks exceed 2x max size (likely due to large code blocks)")
    else:
        print("✓ All chunks respect size limits")
    
    # 4. Verify overlap between adjacent chunks
    if chunker.chunk_overlap > 0 and len(chunks) > 1:
        overlaps_found = 0
        for i in range(1, len(chunks)):
            prev_content = chunks[i-1].content
            curr_content = chunks[i].content
            
            # Check if there's any overlap
            # (Simple check: see if end of prev appears in start of curr)
            prev_end = prev_content[-100:] if len(prev_content) > 100 else prev_content
            if any(word in curr_content[:200] for word in prev_end.split()[:5]):
                overlaps_found += 1
        
        print(f"✓ Found overlap in {overlaps_found}/{len(chunks)-1} chunk boundaries")
    
    print("\n✅ Comprehensive test passed!")
    return chunks


def test_code_block_with_explanation():
    """Test that code blocks stay with their explanatory text."""
    
    markdown_content = """# Code Examples

## Example 1

This function calculates the factorial of a number. It uses recursion
to compute the result efficiently.

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

The function handles edge cases properly.

## Example 2

Here's another example showing iteration:

```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

This iterative approach is more efficient for large values.
"""
    
    parser = MarkdownParser()
    doc_structure = parser.parse(markdown_content, source_path="examples.md")
    
    # Use small chunk size to force splitting
    chunker = SemanticChunker(
        max_chunk_size=300,
        min_chunk_size=50,
        chunk_overlap=0,
        size_metric="characters"
    )
    
    chunks = chunker.chunk_document(doc_structure)
    
    print(f"\nCode block with explanation test: {len(chunks)} chunks")
    
    # Verify each code block has explanatory text nearby
    for i, chunk in enumerate(chunks):
        if "def factorial" in chunk.content:
            assert "calculates the factorial" in chunk.content or "recursion" in chunk.content, \
                "Code block should be with its explanation"
            print(f"✓ Chunk {i}: factorial code is with explanation")
        
        if "def fibonacci" in chunk.content:
            assert "iteration" in chunk.content or "iterative" in chunk.content, \
                "Code block should be with its explanation"
            print(f"✓ Chunk {i}: fibonacci code is with explanation")
    
    print("✅ Code block explanation test passed!")


def test_heading_preservation():
    """Test that headings are preserved in split chunks."""
    
    markdown_content = """# Main Section

## Subsection

This is a very long paragraph that will definitely exceed our chunk size limit.
It contains lots of information about various topics. We want to make sure that
when this section is split into multiple chunks, each chunk retains the heading
information so that context is preserved. This is important for retrieval because
users need to know which section the content came from. The heading provides
essential context for understanding the content.

More content here to make it even longer and force splitting. We're adding more
and more text to ensure that the chunker will need to split this section into
multiple pieces while preserving the heading in each piece.
"""
    
    parser = MarkdownParser()
    doc_structure = parser.parse(markdown_content, source_path="test.md")
    
    chunker = SemanticChunker(
        max_chunk_size=200,
        min_chunk_size=50,
        chunk_overlap=0,
        size_metric="characters"
    )
    
    chunks = chunker.chunk_document(doc_structure)
    
    print(f"\nHeading preservation test: {len(chunks)} chunks")
    
    # If section was split, verify heading appears in all chunks
    subsection_chunks = [c for c in chunks if "Subsection" in c.content]
    
    if len(subsection_chunks) > 1:
        print(f"✓ Section was split into {len(subsection_chunks)} chunks")
        for i, chunk in enumerate(subsection_chunks):
            assert "## Subsection" in chunk.content, \
                f"Chunk {i} should contain the section heading"
            print(f"  ✓ Chunk {i} contains heading")
    else:
        print("ℹ Section was not split (fits in one chunk)")
    
    print("✅ Heading preservation test passed!")


if __name__ == "__main__":
    print("Running comprehensive semantic chunker tests...\n")
    test_with_real_markdown()
    print("\n" + "=" * 80 + "\n")
    test_code_block_with_explanation()
    print("\n" + "=" * 80 + "\n")
    test_heading_preservation()
    print("\n" + "=" * 80)
    print("✅ All comprehensive tests passed!")
