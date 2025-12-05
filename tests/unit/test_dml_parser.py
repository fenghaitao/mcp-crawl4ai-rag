#!/usr/bin/env python3
"""Test script to verify tree-sitter-dml integration with astchunk."""

import sys
from pathlib import Path

# Add tree-sitter-dml to path
dml_path = Path(__file__).parent / "tree-sitter-dml"
if dml_path.exists():
    sys.path.insert(0, str(dml_path / "bindings" / "python"))

# Test importing tree-sitter-dml
try:
    import tree_sitter_dml as tsdml
    print("✓ Successfully imported tree_sitter_dml")
    
    # Test getting the language
    try:
        lang = tsdml.language()
        print(f"✓ Successfully loaded DML language: {lang}")
    except Exception as e:
        print(f"✗ Failed to load DML language: {e}")
        sys.exit(1)
    
    # Test creating a parser
    try:
        import tree_sitter as ts
        parser = ts.Parser(ts.Language(lang))
        print("✓ Successfully created DML parser")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        sys.exit(1)
    
    # Test parsing a simple DML code
    dml_code = """
    dml 1.4;
    device simple_device;
    
    bank regs {
        register r1 size 4 @ 0x00;
    }
    """
    
    try:
        tree = parser.parse(bytes(dml_code, "utf8"))
        print(f"✓ Successfully parsed DML code")
        print(f"  Root node type: {tree.root_node.type}")
        print(f"  Root node children: {len(tree.root_node.children)}")
    except Exception as e:
        print(f"✗ Failed to parse DML code: {e}")
        sys.exit(1)
    
    print("\n✓ All tests passed!")
    
except ImportError as e:
    print(f"✗ Failed to import tree_sitter_dml: {e}")
    print("\nPlease ensure tree-sitter-dml is built:")
    print("  cd tree-sitter-dml")
    print("  npm install")
    print("  npx tree-sitter generate")
    sys.exit(1)
