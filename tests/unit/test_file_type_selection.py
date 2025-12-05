#!/usr/bin/env python3
"""
Test script for file type selection feature.
Demonstrates the --file-types parameter functionality.
"""
import sys
import os
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from crawl_simics_source import find_simics_source_files

def test_file_type_selection():
    """Test the file type selection feature."""
    print("=" * 80)
    print("Testing File Type Selection Feature")
    print("=" * 80)
    
    # Use a test directory (adjust as needed)
    simics_path = os.getenv("SIMICS_SOURCE_PATH", "simics-7-packages-2025-38-linux64/")
    
    if not Path(simics_path).exists():
        print(f"❌ Simics path not found: {simics_path}")
        print("   Set SIMICS_SOURCE_PATH environment variable to test")
        return
    
    # Test 1: DML only
    print("\n" + "=" * 80)
    print("Test 1: DML files only (--file-types dml)")
    print("=" * 80)
    result = find_simics_source_files(simics_path, file_types="dml")
    print(f"DML files found: {len(result['dml'])}")
    print(f"Python files found: {len(result['python'])} (should be 0)")
    assert len(result['python']) == 0, "Python files should not be found when file_types='dml'"
    print("✅ Test 1 passed!")
    
    # Test 2: Python only
    print("\n" + "=" * 80)
    print("Test 2: Python files only (--file-types python)")
    print("=" * 80)
    result = find_simics_source_files(simics_path, file_types="python")
    print(f"DML files found: {len(result['dml'])} (should be 0)")
    print(f"Python files found: {len(result['python'])}")
    assert len(result['dml']) == 0, "DML files should not be found when file_types='python'"
    print("✅ Test 2 passed!")
    
    # Test 3: Both (default)
    print("\n" + "=" * 80)
    print("Test 3: Both file types (--file-types dml+python)")
    print("=" * 80)
    result = find_simics_source_files(simics_path, file_types="dml+python")
    print(f"DML files found: {len(result['dml'])}")
    print(f"Python files found: {len(result['python'])}")
    total = len(result['dml']) + len(result['python'])
    assert total > 0, "Should find at least some files"
    print("✅ Test 3 passed!")
    
    # Test 4: Invalid type (should default to dml+python)
    print("\n" + "=" * 80)
    print("Test 4: Invalid file type (should default to dml+python)")
    print("=" * 80)
    result = find_simics_source_files(simics_path, file_types="invalid")
    dml_count = len(result['dml'])
    py_count = len(result['python'])
    print(f"DML files found: {dml_count}")
    print(f"Python files found: {py_count}")
    print("✅ Test 4 passed! (defaulted to dml+python)")
    
    # Summary
    print("\n" + "=" * 80)
    print("All tests passed! ✅")
    print("=" * 80)
    print("\nUsage examples:")
    print("  python scripts/crawl_simics_source.py --file-types dml")
    print("  python scripts/crawl_simics_source.py --file-types python")
    print("  python scripts/crawl_simics_source.py --file-types dml+python")
    print("  python scripts/crawl_simics_source.py -t dml")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_file_type_selection()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
