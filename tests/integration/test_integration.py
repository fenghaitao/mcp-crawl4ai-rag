#!/usr/bin/env python3
"""
Integration test for user manual pipeline integration.

Tests:
1. Pipeline flag parsing
2. Code summarizer documentation function
3. Database helper function
4. Chunk processing script
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all integration components can be imported."""
    print("Testing imports...")
    
    try:
        from src.code_summarizer import generate_documentation_summary
        print("✅ code_summarizer.generate_documentation_summary")
    except ImportError as e:
        print(f"❌ Failed to import generate_documentation_summary: {e}")
        return False
    
    try:
        from src.utils import add_documentation_chunks_to_supabase
        print("✅ utils.add_documentation_chunks_to_supabase")
    except ImportError as e:
        print(f"❌ Failed to import add_documentation_chunks_to_supabase: {e}")
        return False
    
    try:
        from user_manual_chunker import UserManualChunker
        print("✅ UserManualChunker")
    except ImportError as e:
        print(f"❌ Failed to import UserManualChunker: {e}")
        return False
    
    try:
        from user_manual_chunker.config import ChunkerConfig
        print("✅ ChunkerConfig")
    except ImportError as e:
        print(f"❌ Failed to import ChunkerConfig: {e}")
        return False
    
    return True


def test_code_summarizer_signature():
    """Test that generate_documentation_summary has correct signature."""
    print("\nTesting code_summarizer signature...")
    
    try:
        from src.code_summarizer import generate_documentation_summary
        import inspect
        
        sig = inspect.signature(generate_documentation_summary)
        params = list(sig.parameters.keys())
        
        expected_params = ['chunk', 'doc_context', 'metadata', 'model', 'max_tokens']
        
        for param in expected_params:
            if param in params:
                print(f"✅ Parameter '{param}' present")
            else:
                print(f"❌ Parameter '{param}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking signature: {e}")
        return False


def test_database_helper_signature():
    """Test that add_documentation_chunks_to_supabase has correct signature."""
    print("\nTesting database helper signature...")
    
    try:
        from src.utils import add_documentation_chunks_to_supabase
        import inspect
        
        sig = inspect.signature(add_documentation_chunks_to_supabase)
        params = list(sig.parameters.keys())
        
        expected_params = ['client', 'chunks', 'delete_existing', 'batch_size']
        
        for param in expected_params:
            if param in params:
                print(f"✅ Parameter '{param}' present")
            else:
                print(f"❌ Parameter '{param}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking signature: {e}")
        return False


def test_chunk_script_exists():
    """Test that chunk_user_manuals.py script exists and is executable."""
    print("\nTesting chunk_user_manuals.py script...")
    
    script_path = Path(__file__).parent / "scripts" / "chunk_user_manuals.py"
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    print(f"✅ Script exists: {script_path}")
    
    if not os.access(script_path, os.X_OK):
        print(f"⚠️  Script is not executable (but can still be run with python)")
    else:
        print(f"✅ Script is executable")
    
    return True


def test_migration_files_exist():
    """Test that migration files exist."""
    print("\nTesting migration files...")
    
    migration_sql = Path(__file__).parent / "supabase" / "migrations" / "001_add_documentation_fields.sql"
    migration_readme = Path(__file__).parent / "supabase" / "migrations" / "README.md"
    
    if not migration_sql.exists():
        print(f"❌ Migration SQL not found: {migration_sql}")
        return False
    
    print(f"✅ Migration SQL exists: {migration_sql}")
    
    if not migration_readme.exists():
        print(f"❌ Migration README not found: {migration_readme}")
        return False
    
    print(f"✅ Migration README exists: {migration_readme}")
    
    return True


def test_pipeline_integration():
    """Test that crawl_pipeline.py has --process-manuals flag."""
    print("\nTesting pipeline integration...")
    
    pipeline_path = Path(__file__).parent / "scripts" / "crawl_pipeline.py"
    
    if not pipeline_path.exists():
        print(f"❌ Pipeline script not found: {pipeline_path}")
        return False
    
    with open(pipeline_path, 'r') as f:
        content = f.read()
    
    if '--process-manuals' in content:
        print("✅ --process-manuals flag found in crawl_pipeline.py")
    else:
        print("❌ --process-manuals flag not found in crawl_pipeline.py")
        return False
    
    if 'chunk_user_manuals.py' in content:
        print("✅ chunk_user_manuals.py reference found in crawl_pipeline.py")
    else:
        print("❌ chunk_user_manuals.py reference not found in crawl_pipeline.py")
        return False
    
    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("User Manual Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Code Summarizer Signature", test_code_summarizer_signature),
        ("Database Helper Signature", test_database_helper_signature),
        ("Chunk Script", test_chunk_script_exists),
        ("Migration Files", test_migration_files_exist),
        ("Pipeline Integration", test_pipeline_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
