# PatternAwareSemanticChunker Integration

## Overview

`PatternAwareSemanticChunker` is a new class that extends `SemanticChunker` to add pattern detection capabilities. It automatically detects special documentation structures (API docs, grammar rules, tables, etc.) and ensures they are kept together during chunking.

## Implementation

### Class Hierarchy

```
SemanticChunkerInterface (ABC)
    ↓
SemanticChunker
    ↓
PatternAwareSemanticChunker
```

### Key Features

1. **Inherits all SemanticChunker functionality**
   - Section-based chunking
   - Code block integrity preservation
   - Paragraph boundary splitting
   - Small section merging
   - Chunk overlap

2. **Adds pattern detection**
   - Lists with context
   - API documentation patterns
   - Grammar rules with examples
   - Definition lists
   - Tables
   - Cross-references

3. **Pattern-aware splitting**
   - Checks if content ranges contain special patterns
   - Avoids splitting within detected patterns
   - Keeps related content together even if it exceeds chunk size limits

4. **Optional pattern detection**
   - Can be enabled/disabled via constructor parameter
   - When disabled, behaves exactly like SemanticChunker
   - No performance overhead when disabled

## Usage

### Basic Usage

```python
from src.user_manual_chunker import (
    PatternAwareSemanticChunker,
    MarkdownParser,
    ChunkerConfig
)

# Parse document
parser = MarkdownParser()
doc = parser.parse(content, "manual.md")

# Create pattern-aware chunker
config = ChunkerConfig(max_chunk_size=1000, min_chunk_size=100)
chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)

# Chunk document
chunks = chunker.chunk_document(doc)

# Get pattern statistics
stats = chunker.get_pattern_statistics()
print(f"Detected {stats['total']} patterns")
print(f"  - API docs: {stats['api_docs']}")
print(f"  - Tables: {stats['tables']}")
```

### Drop-in Replacement

```python
# Can be used as a drop-in replacement for SemanticChunker
from src.user_manual_chunker import PatternAwareSemanticChunker

# With patterns enabled (enhanced behavior)
chunker = PatternAwareSemanticChunker(
    max_chunk_size=1000,
    enable_pattern_detection=True
)

# With patterns disabled (same as SemanticChunker)
chunker = PatternAwareSemanticChunker(
    max_chunk_size=1000,
    enable_pattern_detection=False
)
```

### Integration with Orchestrator

```python
from src.user_manual_chunker import (
    UserManualChunker,
    PatternAwareSemanticChunker,
    ChunkerConfig
)

# Create pattern-aware chunker
config = ChunkerConfig()
pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)

# Use with orchestrator
orchestrator = UserManualChunker(
    chunker=pattern_chunker,
    config=config
)

# Process documents with pattern awareness
chunks = orchestrator.process_document("manual.md")
```

## How It Works

### Pattern Detection Phase

When `chunk_document()` is called:

1. **Analyze content** - Runs all pattern handlers to detect special structures
2. **Cache patterns** - Stores detected patterns for use during chunking
3. **Chunk with awareness** - Uses pattern information during splitting decisions
4. **Clear cache** - Removes pattern cache after chunking

### Pattern-Aware Splitting

When splitting at paragraph boundaries:

1. **Accumulate content** - Builds up paragraphs and code blocks
2. **Check size** - Determines if split is needed
3. **Check patterns** - Calls `should_keep_together()` to check for patterns
4. **Make decision**:
   - If patterns found: Keep accumulating (don't split)
   - If no patterns: Split at this boundary

### Pattern Detection Logic

```python
def should_keep_together(line_start, line_end, patterns, max_size):
    """
    Check if a range contains patterns that should stay together.
    
    Returns True if:
    - Range contains a list that should be kept together
    - Range contains API documentation
    - Range contains grammar rules
    - Range contains definition lists
    - Range contains tables
    
    Returns False if:
    - No patterns detected in range
    - Patterns are too large (exceed max_size)
    """
```

## Pattern Types Detected

### 1. Lists
- Nested list structures
- List items with their parent context
- Preserves indentation levels

### 2. API Documentation
- Function signatures
- Parameter descriptions
- Code examples
- Return value documentation

### 3. Grammar Rules
- Grammar rule definitions
- Example code for rules
- Syntax specifications

### 4. Definition Lists
- Terms with definitions
- Glossary entries
- Key-value pairs

### 5. Tables
- Markdown tables
- HTML tables
- Table headers and data

### 6. Cross-References
- Internal links
- External references
- Anchor links

## Performance Considerations

### With Pattern Detection Enabled

- **Overhead**: ~10-20% slower than regular chunking
- **Memory**: Stores pattern cache during chunking
- **Best for**: Technical documentation with special structures

### With Pattern Detection Disabled

- **Overhead**: None (same as SemanticChunker)
- **Memory**: No additional memory usage
- **Best for**: Simple documents or performance-critical scenarios

## Testing

### Unit Tests

All tests in `test_pattern_aware_semantic_chunker.py`:

- ✅ Initialization with patterns enabled/disabled
- ✅ Creating from config
- ✅ Chunking with patterns enabled/disabled
- ✅ Pattern statistics
- ✅ Inheritance from SemanticChunker
- ✅ Drop-in replacement compatibility
- ✅ Real document processing

### Demo Script

Run `demo_pattern_aware_chunker.py` to see:

- Comparison with regular chunker
- Pattern detection in action
- Real document processing
- Enable/disable pattern detection

## API Reference

### Constructor

```python
PatternAwareSemanticChunker(
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100,
    chunk_overlap: int = 50,
    size_metric: str = "characters",
    enable_pattern_detection: bool = True
)
```

**Parameters:**
- `max_chunk_size`: Maximum chunk size in characters/tokens
- `min_chunk_size`: Minimum chunk size for merging
- `chunk_overlap`: Overlap between adjacent chunks
- `size_metric`: "characters" or "tokens"
- `enable_pattern_detection`: Enable/disable pattern detection

### Methods

#### `from_config(config, enable_patterns=True)`

Create chunker from configuration object.

```python
config = ChunkerConfig(max_chunk_size=1000)
chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
```

#### `chunk_document(doc_structure)`

Chunk document with pattern awareness.

```python
chunks = chunker.chunk_document(doc_structure)
```

#### `get_pattern_statistics()`

Get statistics about detected patterns.

```python
stats = chunker.get_pattern_statistics()
# Returns: {'lists': 5, 'api_docs': 3, 'tables': 2, ...}
```

#### `get_detected_patterns()`

Get the raw pattern detection results.

```python
patterns = chunker.get_detected_patterns()
# Returns: {'lists': [...], 'api_docs': [...], ...}
```

## Examples

### Example 1: API Documentation

```python
content = """
### init()
Initialize the device.

```python
device.init()
```
"""

# Regular chunker might split signature from code
regular_chunker = SemanticChunker(max_chunk_size=100)
# Result: 2 chunks (signature separate from code)

# Pattern-aware chunker keeps them together
pattern_chunker = PatternAwareSemanticChunker(max_chunk_size=100)
# Result: 1 chunk (signature + code together)
```

### Example 2: Grammar Rules

```python
content = """
## Variable Declaration

Variables use the `var` keyword:

```
var x: int = 42;
```

Example:
```
var name: string = "Alice";
```
"""

# Pattern-aware chunker detects grammar rule pattern
# and keeps rule + examples together
```

### Example 3: Tables

```python
content = """
| Function | Description |
|----------|-------------|
| init()   | Initialize  |
| reset()  | Reset       |
"""

# Pattern-aware chunker keeps entire table together
# even if it exceeds chunk size slightly
```

## Migration Guide

### From SemanticChunker

```python
# Before
from src.user_manual_chunker import SemanticChunkerImpl as SemanticChunker

chunker = SemanticChunker(max_chunk_size=1000)
chunks = chunker.chunk_document(doc)

# After (with pattern awareness)
from src.user_manual_chunker import PatternAwareSemanticChunker

chunker = PatternAwareSemanticChunker(
    max_chunk_size=1000,
    enable_pattern_detection=True
)
chunks = chunker.chunk_document(doc)

# After (without pattern awareness - same behavior)
chunker = PatternAwareSemanticChunker(
    max_chunk_size=1000,
    enable_pattern_detection=False
)
chunks = chunker.chunk_document(doc)
```

### In Orchestrator

```python
# Before
orchestrator = UserManualChunker.from_config(config)

# After (with pattern awareness)
pattern_chunker = PatternAwareSemanticChunker.from_config(config, enable_patterns=True)
orchestrator = UserManualChunker(chunker=pattern_chunker, config=config)
```

## Future Enhancements

Potential improvements:

1. **Configurable pattern handlers** - Allow users to enable/disable specific patterns
2. **Custom pattern handlers** - Allow users to register custom pattern detectors
3. **Pattern priority** - Allow specifying which patterns take precedence
4. **Pattern size limits** - Configure maximum size for patterns to keep together
5. **Pattern reporting** - Detailed reporting of which patterns affected chunking decisions

## Conclusion

`PatternAwareSemanticChunker` provides an enhanced chunking experience for technical documentation by automatically detecting and preserving special structures. It's a drop-in replacement for `SemanticChunker` with optional pattern detection that can be enabled or disabled based on your needs.

**Key Benefits:**
- ✅ Preserves API documentation integrity
- ✅ Keeps grammar rules with examples
- ✅ Maintains table structures
- ✅ Preserves definition lists
- ✅ Optional - can be disabled for performance
- ✅ Drop-in replacement for SemanticChunker
- ✅ Fully tested and documented
