# ASTChunk DML Integration Update

## Summary

Updated astchunk to properly use tree-sitter-dml for parsing DML (Device Modeling Language) source code. The integration now uses the Python bindings from the tree-sitter-dml submodule.

## Changes Made

### 1. Updated `astchunk/src/astchunk/astchunk_builder.py`

**Import Changes:**
- Added proper import for `tree_sitter_dml` package
- Implemented fallback mechanism to load from local tree-sitter-dml directory if package not installed
- Removed hardcoded path manipulation in favor of standard Python package import

**DML Parser Initialization:**
- Replaced manual `.so` file loading with proper tree-sitter-dml package usage
- Now uses `ts.Language(tsdml.language())` to get the DML language
- Added clear error messages if tree-sitter-dml is not installed

**Before:**
```python
elif self.language == "dml":
    # Load DML parser from local tree-sitter-dml directory
    try:
        from tree_sitter import Language
        dml_so = dml_path / "build" / "dml.so"
        if not dml_so.exists():
            raise FileNotFoundError(f"DML parser not found. Run 'tree-sitter generate' in {dml_path}")
        dml_lang = Language(str(dml_so), "dml")
        self.parser = ts.Parser(dml_lang)
    except Exception as e:
        raise ValueError(f"Failed to load DML parser: {e}")
```

**After:**
```python
elif self.language == "dml":
    # Load DML parser using tree-sitter-dml package
    if tsdml is None:
        raise ValueError(
            "tree-sitter-dml is not installed. Please install it:\n"
            "  cd tree-sitter-dml && pip install -e .\n"
            "Or install from the parent directory:\n"
            "  pip install -e tree-sitter-dml"
        )
    try:
        self.parser = ts.Parser(ts.Language(tsdml.language()))
    except Exception as e:
        raise ValueError(f"Failed to load DML parser: {e}")
```

### 2. Updated `astchunk/requirements.txt`

- Updated comment to clarify that tree-sitter-dml should be installed separately
- Added installation instructions

### 3. Updated `astchunk/pyproject.toml`

- Updated dependency comments to clarify tree-sitter-dml installation
- Maintained compatibility with existing dependencies

## Installation Instructions

### Option 1: Install tree-sitter-dml from local directory

```bash
# From the project root
pip install -e tree-sitter-dml
```

### Option 2: Install tree-sitter-dml with uv (if using virtual environment)

```bash
# Create virtual environment if needed
uv venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install tree-sitter-dml
uv pip install -e tree-sitter-dml
```

### Option 3: Use without installation (fallback)

The code includes a fallback mechanism that will automatically add the tree-sitter-dml bindings to the Python path if the package is not installed. This works as long as the tree-sitter-dml directory exists in the expected location.

## Testing

### Test DML Parser Integration

Run the existing test script:

```bash
python3 test_astchunk_integration.py
```

This will test:
1. Python code chunking (baseline)
2. DML code chunking (new functionality)
3. Fallback mechanism for unsupported languages

### Expected Output

```
🧪 Testing ASTChunk Integration

============================================================
Testing Python Code Chunking
============================================================
✅ Generated X chunks

--- Chunk 1 ---
Content length: XXX chars
Lines: X-X
File: test_calculator.py
Content preview: ...

============================================================
Testing DML Code Chunking
============================================================
✅ Generated X chunks

--- Chunk 1 ---
Content length: XXX chars
Lines: X-X
File: test_uart.dml
Content preview: ...

============================================================
Testing Fallback for Unsupported Language
============================================================
✅ Fallback worked, generated X chunk(s)

============================================================
Test Results
============================================================
Python Chunking: ✅ PASS
DML Chunking: ✅ PASS
Fallback Mechanism: ✅ PASS
============================================================

🎉 All tests passed!
```

## How It Works

### DML Language Support

The tree-sitter-dml package provides Python bindings for the DML tree-sitter grammar. The integration works as follows:

1. **Import**: `import tree_sitter_dml as tsdml`
2. **Get Language**: `lang = tsdml.language()`
3. **Create Parser**: `parser = ts.Parser(ts.Language(lang))`
4. **Parse Code**: `tree = parser.parse(bytes(code, "utf8"))`

### Fallback Mechanism

If tree-sitter-dml is not installed as a package, the code will:
1. Check if the tree-sitter-dml directory exists
2. Add `tree-sitter-dml/bindings/python` to sys.path
3. Import tree_sitter_dml from that location

This allows the code to work in development environments without requiring package installation.

## Architecture

```
mcp-crawl4ai-rag/
├── astchunk/                          # AST chunking library
│   └── src/astchunk/
│       └── astchunk_builder.py        # ✓ Updated to use tree-sitter-dml
├── tree-sitter-dml/                   # DML parser (git submodule)
│   └── bindings/python/
│       └── tree_sitter_dml/
│           ├── __init__.py            # Language loader
│           └── binding.py             # C bindings
├── src/
│   └── crawl4ai_mcp.py               # Uses smart_chunk_source()
└── test_astchunk_integration.py      # Integration tests
```

## Benefits

1. **Proper Package Structure**: Uses standard Python package imports instead of manual path manipulation
2. **Better Error Messages**: Clear instructions when tree-sitter-dml is not available
3. **Fallback Support**: Works in development without package installation
4. **Maintainability**: Follows Python best practices for package dependencies
5. **Flexibility**: Supports both installed package and local development modes

## Troubleshooting

### Error: "tree-sitter-dml is not installed"

**Solution**: Install tree-sitter-dml:
```bash
pip install -e tree-sitter-dml
```

### Error: "No module named 'tree_sitter'"

**Solution**: Install tree-sitter:
```bash
pip install tree-sitter
```

### Error: "Failed to load DML language"

**Solution**: Ensure tree-sitter-dml is properly built:
```bash
cd tree-sitter-dml
npm install
npx tree-sitter generate
```

### Parser Not Working

**Check**:
1. tree-sitter-dml/src/parser.c exists
2. tree-sitter-dml/bindings/python/tree_sitter_dml/__init__.py exists
3. Python can import tree_sitter_dml

## Next Steps

1. **Test in Production**: Run the integration tests in your environment
2. **Update Documentation**: Update any user-facing documentation about DML support
3. **CI/CD Integration**: Add tree-sitter-dml installation to CI/CD pipelines
4. **Performance Testing**: Test with large DML files to ensure chunking performance

## Related Files

- `ASTCHUNK_DML_INTEGRATION.md` - Original integration guide
- `ASTCHUNK_INTEGRATION_GUIDE.md` - General astchunk integration guide
- `QUICK_START_DML.md` - Quick start guide for DML support
- `astchunk/DML_SUPPORT.md` - DML support documentation in astchunk
