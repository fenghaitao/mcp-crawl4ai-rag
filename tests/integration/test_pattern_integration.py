"""
Integration test for pattern handlers with semantic chunker.

This test demonstrates how the pattern handlers preserve special
documentation structures during chunking.
"""

from src.user_manual_chunker import (
    MarkdownParser,
    SemanticChunkerImpl,
    PatternAwareChunker,
)


def test_list_preservation_in_chunks():
    """Test that lists are preserved with their context."""
    content = """# API Methods

The following methods are available:

- `get(key)`: Retrieve a value
- `set(key, value)`: Store a value
- `delete(key)`: Remove a value
- `clear()`: Remove all values

Each method returns a status code.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    chunker = SemanticChunkerImpl(max_chunk_size=500, min_chunk_size=50)
    chunks = chunker.chunk_document(doc)
    
    print(f"✓ Created {len(chunks)} chunk(s)")
    
    # Verify list items are in the chunk
    chunk_content = chunks[0].content
    assert "- `get(key)`" in chunk_content, "List item should be preserved"
    assert "- `set(key, value)`" in chunk_content, "List item should be preserved"
    assert "The following methods are available:" in chunk_content, "Context should be preserved"
    
    print("✓ List items preserved with context")


def test_api_documentation_preservation():
    """Test that API documentation patterns are preserved."""
    content = """# Functions

## add

Adds two numbers together.

```python
def add(a, b):
    return a + b
```

## multiply

Multiplies two numbers.

```python
def multiply(a, b):
    return a * b
```
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['api_docs'])} API documentation pattern(s)")
    assert len(patterns['api_docs']) == 2, "Should detect both function definitions"
    
    # Verify function signatures are detected
    signatures = [api.signature for api in patterns['api_docs']]
    assert any("def add" in sig for sig in signatures), "Should detect add function"
    assert any("def multiply" in sig for sig in signatures), "Should detect multiply function"
    
    print("✓ API documentation patterns detected correctly")


def test_table_preservation():
    """Test that tables are preserved in chunks."""
    content = """# Configuration Options

The following table shows available options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| host   | str  | localhost | Server host |
| port   | int  | 8080    | Server port |
| debug  | bool | false   | Debug mode  |

These options can be set in the config file.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['tables'])} table(s)")
    assert len(patterns['tables']) == 1, "Should detect the table"
    
    table = patterns['tables'][0]
    assert "| Option | Type |" in table.content, "Table header should be preserved"
    assert table.format_type == "markdown", "Should detect markdown format"
    
    print("✓ Table structure preserved")


def test_definition_list_preservation():
    """Test that definition lists are preserved."""
    content = """# Glossary

API: Application Programming Interface
SDK: Software Development Kit
REST: Representational State Transfer
JSON: JavaScript Object Notation

These terms are used throughout the documentation.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['definitions'])} definition(s)")
    assert len(patterns['definitions']) == 4, "Should detect all definitions"
    
    # Verify definitions
    terms = [d.term for d in patterns['definitions']]
    assert "API" in terms, "Should detect API definition"
    assert "SDK" in terms, "Should detect SDK definition"
    
    print("✓ Definition lists detected correctly")


def test_cross_reference_preservation():
    """Test that cross-references are preserved."""
    content = """# Documentation

For more information, see the [API Reference](api.md).

You can also check the [User Guide](guide.md) for examples.

External resources: [Python Docs](https://docs.python.org)
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['references'])} cross-reference(s)")
    assert len(patterns['references']) == 3, "Should detect all links"
    
    # Verify references
    refs = [(r.text, r.target) for r in patterns['references']]
    assert any("API Reference" in text for text, _ in refs), "Should detect API Reference link"
    assert any("api.md" in target for _, target in refs), "Should detect api.md target"
    
    print("✓ Cross-references preserved")


def test_grammar_specification_preservation():
    """Test that grammar specifications are preserved."""
    content = """# Grammar

Expression ::= Term ('+' Term)*
  Example: 1 + 2 + 3

Term ::= Factor ('*' Factor)*
  Example: 2 * 3

Factor ::= Number | '(' Expression ')'
  Example: (1 + 2) * 3
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['grammar_rules'])} grammar rule(s)")
    assert len(patterns['grammar_rules']) == 3, "Should detect all grammar rules"
    
    # Verify rules have examples
    for rule in patterns['grammar_rules']:
        assert len(rule.examples) > 0, f"Rule '{rule.rule}' should have examples"
    
    print("✓ Grammar rules with examples preserved")


def test_nested_list_preservation():
    """Test that nested lists are preserved correctly."""
    content = """# Features

Main features:

- Authentication
  - Username/password
  - OAuth2
  - API keys
- Data storage
  - SQL databases
  - NoSQL databases
- Caching
  - Redis
  - Memcached

All features are production-ready.
"""
    
    parser = MarkdownParser()
    doc = parser.parse(content, "test.md")
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print(f"✓ Detected {len(patterns['lists'])} list item(s)")
    
    # Verify nested structure
    list_items = patterns['lists']
    levels = [item.level for item in list_items]
    assert 0 in levels, "Should have top-level items"
    assert 1 in levels, "Should have nested items"
    
    print("✓ Nested list structure preserved")


if __name__ == "__main__":
    print("Testing pattern handler integration with semantic chunker...\n")
    print("=" * 70)
    
    test_list_preservation_in_chunks()
    print()
    
    test_api_documentation_preservation()
    print()
    
    test_table_preservation()
    print()
    
    test_definition_list_preservation()
    print()
    
    test_cross_reference_preservation()
    print()
    
    test_grammar_specification_preservation()
    print()
    
    test_nested_list_preservation()
    print()
    
    print("=" * 70)
    print("✅ All pattern integration tests passed!")
    print("=" * 70)
