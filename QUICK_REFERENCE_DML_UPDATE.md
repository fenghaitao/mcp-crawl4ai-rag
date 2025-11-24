# Quick Reference: ASTChunk DML Update

## What Changed?

Updated astchunk to use tree-sitter-dml Python package instead of manual `.so` file loading.

## Installation

```bash
pip install -e tree-sitter-dml
```

## Usage

```python
from astchunk import ASTChunkBuilder

# Create DML chunker
chunker = ASTChunkBuilder(
    max_chunk_size=800,
    language="dml",
    metadata_template="default"
)

# Chunk DML code
chunks = chunker.chunkify(
    code=dml_code,
    chunk_overlap=1,
    repo_level_metadata={"file_path": "device.dml"}
)
```

## Testing

```bash
# Test integration
python3 test_astchunk_integration.py

# Run demo
python3 demo_dml_chunking.py
```

## Files Changed

- ✓ `astchunk/src/astchunk/astchunk_builder.py` - Updated DML parser loading
- ✓ `astchunk/requirements.txt` - Updated comments
- ✓ `astchunk/pyproject.toml` - Updated comments

## Files Created

- ✓ `ASTCHUNK_DML_UPDATE.md` - Detailed documentation
- ✓ `CHANGES_SUMMARY.md` - Summary of changes
- ✓ `demo_dml_chunking.py` - Demo script
- ✓ `test_dml_parser.py` - Test script
- ✓ `QUICK_REFERENCE_DML_UPDATE.md` - This file

## Key Benefits

✓ Standard Python imports
✓ Better error messages
✓ Fallback mechanism
✓ Backward compatible

## Troubleshooting

| Error | Solution |
|-------|----------|
| "tree-sitter-dml is not installed" | `pip install -e tree-sitter-dml` |
| "No module named 'tree_sitter'" | `pip install tree-sitter` |
| Import errors | Check Python path, verify bindings exist |

## More Info

See `ASTCHUNK_DML_UPDATE.md` for complete documentation.
