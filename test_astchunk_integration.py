#!/usr/bin/env python3
"""
Test script for astchunk integration in mcp-crawl4ai-rag.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from crawl4ai_mcp import smart_chunk_source

# Test data
PYTHON_CODE = """
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        '''Add two numbers.'''
        return a + b
    
    def multiply(self, a, b):
        '''Multiply two numbers.'''
        return a * b

def main():
    calc = Calculator()
    print(calc.add(2, 3))
    print(calc.multiply(4, 5))

if __name__ == '__main__':
    main()
"""

DML_CODE = """
device uart;
bitorder le;

constant FIFO_SIZE = 16;

template logged_register {
    param size = 4;
    
    method after_write(uint64 value) {
        log info: "Register written: 0x%x", value;
    }
}

bank regs {
    register ctrl size 4 @ 0x00 is (logged_register) {
        field enable @ [0];
        field mode @ [2:1];
    }
    
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
    }
}

method init() {
    log info: "UART device initialized";
    regs.ctrl.enable = 0;
}
"""

def test_python_chunking():
    """Test Python code chunking."""
    print("=" * 60)
    print("Testing Python Code Chunking")
    print("=" * 60)
    
    chunks = smart_chunk_source(
        code=PYTHON_CODE,
        source_type="python",
        max_chunk_size=512,
        chunk_overlap=1,
        file_path="test_calculator.py"
    )
    
    print(f"✅ Generated {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"Content length: {len(chunk['content'])} chars")
        if chunk.get('metadata'):
            meta = chunk['metadata']
            print(f"Lines: {meta.get('start_line', '?')}-{meta.get('end_line', '?')}")
            print(f"File: {meta.get('file_path', 'N/A')}")
        print(f"Content preview: {chunk['content'][:100]}...")
        print()
    
    return len(chunks) > 0

def test_dml_chunking():
    """Test DML code chunking."""
    print("=" * 60)
    print("Testing DML Code Chunking")
    print("=" * 60)
    
    chunks = smart_chunk_source(
        code=DML_CODE,
        source_type="dml",
        max_chunk_size=512,
        chunk_overlap=1,
        file_path="test_uart.dml"
    )
    
    print(f"✅ Generated {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"Content length: {len(chunk['content'])} chars")
        if chunk.get('metadata'):
            meta = chunk['metadata']
            print(f"Lines: {meta.get('start_line', '?')}-{meta.get('end_line', '?')}")
            print(f"File: {meta.get('file_path', 'N/A')}")
        print(f"Content preview: {chunk['content'][:100]}...")
        print()
    
    return len(chunks) > 0

def test_fallback():
    """Test fallback to markdown chunking for unsupported language."""
    print("=" * 60)
    print("Testing Fallback for Unsupported Language")
    print("=" * 60)
    
    chunks = smart_chunk_source(
        code="Some random text",
        source_type="unsupported",
        max_chunk_size=512
    )
    
    print(f"✅ Fallback worked, generated {len(chunks)} chunk(s)\n")
    return len(chunks) > 0

def main():
    """Run all tests."""
    print("\n🧪 Testing ASTChunk Integration\n")
    
    results = {
        "Python Chunking": test_python_chunking(),
        "DML Chunking": test_dml_chunking(),
        "Fallback Mechanism": test_fallback()
    }
    
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
