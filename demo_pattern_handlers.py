"""
Demonstration of pattern handlers with real-world documentation examples.

This script shows how the pattern handlers detect and preserve various
documentation structures from actual user manuals.
"""

from src.user_manual_chunker import (
    MarkdownParser,
    SemanticChunkerImpl,
    PatternAwareChunker,
)


def demo_simics_style_documentation():
    """Demonstrate pattern handling with Simics-style documentation."""
    
    # Example from Simics DML manual style
    content = """# DML Language Reference

## Data Types

DML supports the following built-in data types:

- `int`: Integer type (signed)
  - Size: 32 or 64 bits depending on platform
  - Range: -2^31 to 2^31-1 (32-bit)
- `uint`: Unsigned integer type
  - Size: 32 or 64 bits
  - Range: 0 to 2^32-1 (32-bit)
- `bool`: Boolean type
  - Values: true or false
- `string`: String type

### Type Declarations

Variables are declared with explicit types:

```dml
device simple_device;

bank regs {
    register control size 4 @ 0x00 {
        field enable @ [0];
        field mode @ [2:1];
    }
}
```

The `register` keyword declares a memory-mapped register.

## Method Definitions

Methods are defined using the following syntax:

```dml
method read() -> (uint64) {
    return this.value;
}
```

### Method Parameters

Parameter syntax:

```
method_name(param1: type1, param2: type2) -> (return_type)
```

Example with multiple parameters:

```dml
method write(uint64 value, uint32 offset) -> (bool) {
    if (offset < this.size) {
        this.data[offset] = value;
        return true;
    }
    return false;
}
```

## Grammar Reference

The DML grammar for method declarations:

MethodDecl ::= 'method' Identifier '(' ParamList? ')' '->' '(' TypeList ')' Block
  Example: method read() -> (uint64) { ... }

ParamList ::= Param (',' Param)*
  Example: uint64 value, uint32 offset

Param ::= Type Identifier
  Example: uint64 value

## API Reference

### Core Methods

read(): Read register value
  Returns the current value of the register.
  
write(value): Write register value
  Parameters:
    - value: The value to write (uint64)
  Returns: Success status (bool)

reset(): Reset register to default
  Resets all fields to their default values.

## Configuration Table

| Register | Offset | Size | Access | Description |
|----------|--------|------|--------|-------------|
| CONTROL  | 0x00   | 4    | RW     | Control register |
| STATUS   | 0x04   | 4    | RO     | Status register |
| DATA     | 0x08   | 8    | RW     | Data register |

For more details, see the [DML 1.4 Specification](dml-spec.md).
"""
    
    print("=" * 80)
    print("SIMICS-STYLE DOCUMENTATION ANALYSIS")
    print("=" * 80)
    print()
    
    # Parse the document
    parser = MarkdownParser()
    doc = parser.parse(content, "dml_reference.md")
    
    print(f"Document structure:")
    print(f"  - Headings: {len(doc.headings)}")
    print(f"  - Paragraphs: {len(doc.paragraphs)}")
    print(f"  - Code blocks: {len(doc.code_blocks)}")
    print()
    
    # Analyze patterns
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print("Detected patterns:")
    print(f"  ✓ Lists: {len(patterns['lists'])} items")
    print(f"  ✓ API documentation: {len(patterns['api_docs'])} patterns")
    print(f"  ✓ Grammar rules: {len(patterns['grammar_rules'])} rules")
    print(f"  ✓ Definitions: {len(patterns['definitions'])} terms")
    print(f"  ✓ Tables: {len(patterns['tables'])} tables")
    print(f"  ✓ Cross-references: {len(patterns['references'])} links")
    print()
    
    # Show details of detected patterns
    if patterns['lists']:
        print("List items detected:")
        for i, item in enumerate(patterns['lists'][:5], 1):  # Show first 5
            indent = "  " * item.level
            print(f"  {i}. {indent}[Level {item.level}] {item.content[:60]}...")
        if len(patterns['lists']) > 5:
            print(f"  ... and {len(patterns['lists']) - 5} more")
        print()
    
    if patterns['api_docs']:
        print("API documentation patterns:")
        for i, api in enumerate(patterns['api_docs'], 1):
            print(f"  {i}. Function: {api.signature[:50]}...")
            print(f"     Description: {api.description[:60]}...")
        print()
    
    if patterns['grammar_rules']:
        print("Grammar rules:")
        for i, rule in enumerate(patterns['grammar_rules'], 1):
            print(f"  {i}. {rule.rule}")
            if rule.examples:
                print(f"     Example: {rule.examples[0][:60]}...")
        print()
    
    if patterns['definitions']:
        print("Definitions:")
        for i, defn in enumerate(patterns['definitions'][:5], 1):
            print(f"  {i}. {defn.term}: {defn.definition[:50]}...")
        if len(patterns['definitions']) > 5:
            print(f"  ... and {len(patterns['definitions']) - 5} more")
        print()
    
    if patterns['tables']:
        print("Tables:")
        for i, table in enumerate(patterns['tables'], 1):
            lines = table.content.split('\n')
            print(f"  {i}. {table.format_type.upper()} table ({len(lines)} lines)")
            print(f"     Preview: {lines[0][:60]}...")
        print()
    
    if patterns['references']:
        print("Cross-references:")
        for i, ref in enumerate(patterns['references'], 1):
            print(f"  {i}. [{ref.text}] -> {ref.target}")
        print()
    
    # Create chunks
    chunker = SemanticChunkerImpl(max_chunk_size=800, min_chunk_size=100)
    chunks = chunker.chunk_document(doc)
    
    print(f"Created {len(chunks)} chunks")
    print()
    
    # Show chunk summary
    print("Chunk summary:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}:")
        print(f"    - Lines: {chunk.line_start}-{chunk.line_end}")
        print(f"    - Size: {len(chunk.content)} characters")
        print(f"    - Section: {chunk.section.heading.text}")
        
        # Check what patterns are in this chunk
        chunk_patterns = []
        for list_item in patterns['lists']:
            if chunk.line_start <= list_item.line_start <= chunk.line_end:
                chunk_patterns.append("list")
                break
        
        for api in patterns['api_docs']:
            if chunk.line_start <= api.line_start <= chunk.line_end:
                chunk_patterns.append("api")
                break
        
        for table in patterns['tables']:
            if chunk.line_start <= table.line_start <= chunk.line_end:
                chunk_patterns.append("table")
                break
        
        if chunk_patterns:
            print(f"    - Contains: {', '.join(chunk_patterns)}")
        print()
    
    print("=" * 80)
    print()


def demo_api_reference_documentation():
    """Demonstrate pattern handling with API reference documentation."""
    
    content = """# REST API Reference

## Authentication

All API requests require authentication using an API key.

### API Key Format

API keys follow this format:

```
sk_live_<32_character_string>
sk_test_<32_character_string>
```

## Endpoints

### GET /api/users

Retrieve a list of users.

**Parameters:**

- limit: Maximum number of results (default: 10)
- offset: Pagination offset (default: 0)
- sort: Sort field (default: created_at)

**Response:**

```json
{
  "users": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "total": 2
}
```

### POST /api/users

Create a new user.

**Request Body:**

```json
{
  "name": "Charlie",
  "email": "charlie@example.com"
}
```

**Response:**

```json
{
  "id": 3,
  "name": "Charlie",
  "email": "charlie@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200  | OK      | Request succeeded |
| 201  | Created | Resource created |
| 400  | Bad Request | Invalid parameters |
| 401  | Unauthorized | Authentication failed |
| 404  | Not Found | Resource not found |

For more information, see the [Authentication Guide](auth.md).
"""
    
    print("=" * 80)
    print("API REFERENCE DOCUMENTATION ANALYSIS")
    print("=" * 80)
    print()
    
    parser = MarkdownParser()
    doc = parser.parse(content, "api_reference.md")
    
    pattern_chunker = PatternAwareChunker()
    patterns = pattern_chunker.analyze_content(content, doc.paragraphs, doc.code_blocks)
    
    print("Detected patterns:")
    print(f"  ✓ Lists: {len(patterns['lists'])} items")
    print(f"  ✓ Code blocks: {len(doc.code_blocks)} blocks")
    print(f"  ✓ Tables: {len(patterns['tables'])} tables")
    print(f"  ✓ Cross-references: {len(patterns['references'])} links")
    print()
    
    # Show code blocks with their context
    print("Code blocks with context:")
    for i, cb in enumerate(doc.code_blocks, 1):
        print(f"  {i}. Language: {cb.language}")
        if cb.preceding_text:
            print(f"     Context: {cb.preceding_text[:60]}...")
        print(f"     Lines: {cb.line_start}-{cb.line_end}")
        print()
    
    print("=" * 80)
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PATTERN HANDLERS DEMONSTRATION" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    demo_simics_style_documentation()
    demo_api_reference_documentation()
    
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "DEMONSTRATION COMPLETE" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
