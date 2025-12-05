# Fix: Code Example Extraction for Source Files

## Issue Identified

The `crawl_simics_source.py` script was incorrectly attempting to extract code examples from raw source code files (.dml and .py) using the `extract_code_blocks()` function, which is designed for **markdown content** with triple backticks (```).

### Problem

```python
# BEFORE - INCORRECT
code_blocks = extract_code_blocks(content)  # content is raw .dml or .py file
```

The `extract_code_blocks()` function in `utils.py`:
- Searches for markdown code blocks delimited by triple backticks (```)
- Extracts code between backticks along with surrounding context
- **Not suitable for raw source code files**

### Why This Was Wrong

1. **Source code files don't have markdown formatting** - They are pure code without triple backticks
2. **extract_code_blocks() would return empty results** - No backticks found in .dml or .py files
3. **Unnecessary processing** - The entire file is already code
4. **AST chunks already provide structured code** - The AST-aware chunking already creates meaningful code segments

## Solution

Removed the code example extraction logic for source code files since:

1. **AST chunks are better** - They respect code structure (functions, classes, methods, etc.)
2. **No need for markdown parsing** - Source files are already pure code
3. **Cleaner architecture** - Code examples are for documentation, AST chunks are for source code

### Changes Made

#### 1. Removed Code Example Extraction

```python
# AFTER - CORRECT
# Extract code examples if enabled
# Note: For source code files (.dml, .py), we skip markdown-style code block extraction
# since the entire file is already code. The AST chunks provide well-structured code segments.
# Code example extraction is designed for markdown documentation files.
if agentic_rag_enabled:
    # Skip code example extraction for source code files
    # The AST-aware chunks already provide meaningful code segments
    logging.debug(f"    ℹ️  Skipping code example extraction for source file (using AST chunks instead)")
    pass
```

#### 2. Removed Unused Variables

Removed initialization of:
- `all_code_urls`
- `all_code_chunk_numbers`
- `all_code_examples`
- `all_code_summaries`
- `all_code_metadatas`

#### 3. Removed Unused Imports

Removed:
- `extract_code_blocks`
- `generate_code_example_summary`
- `add_code_examples_to_supabase`
- `ThreadPoolExecutor`

#### 4. Removed Code Example Storage

Removed the section that stored code examples to Supabase since we're not extracting them.

## Architecture

### Before (Incorrect)

```
Source File (.dml/.py)
    ↓
extract_code_blocks() ← WRONG! Looks for markdown backticks
    ↓
No results (no backticks in source files)
    ↓
Wasted processing
```

### After (Correct)

```
Source File (.dml/.py)
    ↓
smart_chunk_source() with AST-aware chunking
    ↓
Well-structured code chunks (functions, classes, methods)
    ↓
Stored in Supabase with rich metadata
```

## Benefits

✅ **Correct Logic** - No longer tries to extract markdown from source code
✅ **Better Performance** - Removed unnecessary processing
✅ **Cleaner Code** - Removed unused variables and imports
✅ **Better Results** - AST chunks provide more meaningful code segments
✅ **Proper Separation** - Code examples for docs, AST chunks for source

## When to Use Each Approach

### Use `extract_code_blocks()` for:
- ✅ Markdown documentation files (.md)
- ✅ HTML pages with code examples
- ✅ Tutorial content with embedded code
- ✅ API documentation with code snippets

### Use AST-aware chunking for:
- ✅ Source code files (.py, .dml, .java, .ts, etc.)
- ✅ When you need structure-aware segmentation
- ✅ When you want to preserve function/class boundaries
- ✅ When you need rich AST metadata

## Example: What Gets Stored

### For a DML File

**Input:** `uart_device.dml` (500 lines)

**AST Chunks Created:**
1. Chunk 1: Device declaration + imports + constants
2. Chunk 2: Register bank definitions
3. Chunk 3: Method implementations
4. Chunk 4: Event handlers

**Metadata Included:**
- File path, line numbers
- Device name, templates used
- Register groups, methods
- AST structure information

**Code Examples:** None (not needed - chunks are already code)

### For a Markdown Documentation File

**Input:** `simics_tutorial.md` (with code examples)

**AST Chunks:** Not applicable (not source code)

**Code Examples Extracted:**
1. Example 1: Python script showing device initialization
2. Example 2: DML code snippet for register definition
3. Example 3: Command-line usage example

**Metadata Included:**
- Context before/after each example
- Language identifier
- Code length

## Testing

The fix has been applied and the script will now:
1. ✅ Correctly chunk DML and Python source files using AST
2. ✅ Skip inappropriate markdown code block extraction
3. ✅ Store well-structured code chunks with metadata
4. ✅ Avoid wasted processing on non-existent markdown blocks

## Related Files

- `scripts/crawl_simics_source.py` - Fixed
- `src/utils.py` - `extract_code_blocks()` unchanged (still used for markdown docs)
- `src/crawl4ai_mcp.py` - `smart_chunk_source()` unchanged (working correctly)

## Conclusion

The code example extraction logic has been corrected to skip source code files, which are already properly handled by AST-aware chunking. This results in cleaner code, better performance, and more appropriate data storage.
