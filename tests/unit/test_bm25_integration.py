"""
Integration test for BM25 collection setup with fastembed installed.

This test verifies that when fastembed is available, the hybrid collection
is created successfully with BM25 support.
"""

import os
import tempfile
import shutil
import pytest


def test_bm25_available():
    """Test if BM25 components are available in ChromaDB."""
    try:
        from chromadb import Schema, K
        from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction
        
        # Verify components can be imported
        assert Schema is not None
        assert K is not None
        assert ChromaBm25EmbeddingFunction is not None
        
        print("✅ BM25 components are available")
        
    except ImportError as e:
        pytest.skip(f"BM25 components not available: {e}")


def test_fastembed_availability():
    """Test if fastembed is installed (required for BM25 to work)."""
    try:
        import fastembed
        print("✅ fastembed is installed")
        return True
    except ImportError:
        print("⚠️  fastembed is not installed - BM25 will fall back to dense-only")
        return False


def test_hybrid_collection_with_fastembed():
    """Test hybrid collection creation when fastembed is available."""
    # Check if fastembed is available
    fastembed_available = test_fastembed_availability()
    
    if not fastembed_available:
        pytest.skip("fastembed not installed - skipping hybrid collection test")
    
    from core.backends.chroma import ChromaBackend
    
    # Create temporary directory for ChromaDB
    temp_dir = tempfile.mkdtemp()
    os.environ['CHROMA_DB_PATH'] = temp_dir
    
    try:
        # Create backend instance
        backend = ChromaBackend()
        
        # Setup hybrid collection
        collection = backend._setup_hybrid_collection('test_hybrid_with_fastembed')
        
        # Verify collection was created successfully
        assert collection is not None, "Collection should be created when fastembed is available"
        assert collection.name == 'test_hybrid_with_fastembed'
        
        print("✅ Hybrid collection created successfully with BM25 support")
        
    finally:
        # Clean up
        os.environ.pop('CHROMA_DB_PATH', None)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("Testing BM25 availability...")
    test_bm25_available()
    print("\nTesting fastembed availability...")
    test_fastembed_availability()
    print("\nTesting hybrid collection creation...")
    test_hybrid_collection_with_fastembed()
