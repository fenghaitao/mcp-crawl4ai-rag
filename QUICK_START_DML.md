# Quick Start: Using ASTChunk with DML

## 1. Setup (One-time)

```bash
# Generate the DML parser
cd tree-sitter-dml
tree-sitter generate
cd ..
```

## 2. Basic Usage

```python
from astchunk import ASTChunkBuilder

# Your DML code
dml_code = """
device uart;

bank regs {
    register ctrl size 4 @ 0x00 {
        field enable @ [0];
    }
}
"""

# Create builder
builder = ASTChunkBuilder(
    max_chunk_size=512,
    language="dml",
    metadata_template="default"
)

# Generate chunks
chunks = builder.chunkify(dml_code)

# Use chunks
for chunk in chunks:
    print(chunk["content"])
```

## 3. Chunk a DML File

```python
from pathlib import Path

# Read file
dml_code = Path("devices/uart.dml").read_text()

# Chunk it
chunks = builder.chunkify(
    code=dml_code,
    repo_level_metadata={"file_path": "devices/uart.dml"}
)

print(f"Created {len(chunks)} chunks")
```

## 4. Test It

```bash
cd astchunk
python tests/test_dml_support.py
```

## That's It!

See `astchunk/DML_SUPPORT.md` for advanced usage.
