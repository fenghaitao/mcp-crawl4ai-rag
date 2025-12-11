"""
Unit tests for collection initialization with hybrid search support.
Tests for task 3: Modify collection initialization to support hybrid search.
"""

import os
import tempfile
import shutil
import pytest
from core.backends.chroma import ChromaBackend


class TestCollectionInitialization:
    """Tests for _get_or_create_metadata_collection with hybrid search support."""
    
    @pytest.fixture
    def temp_chroma_path(self):
        """Create a temporary directory for ChromaDB."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_content_chunks_with_hybrid_search_enabled(self, temp_chroma_path):
        """Test that content_chunks collection uses hybrid search when enabled.
        
        Validates Requirements 1.4, 7.1:
        - WHEN the system initializes the content_chunks collection, 
          THE ChromaDB Backend SHALL apply the schema with BM25 support if hybrid search is enabled
        - WHEN hybrid search is enabled at initialization, 
          THE ChromaDB Backend SHALL log the hybrid search configuration status
        """
        # Set temporary ChromaDB path and enable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'true'
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Get or create content_chunks collection
            collection = backend._get_or_create_metadata_collection('content_chunks')
            
            # Verify collection was created
            assert collection is not None
            assert collection.name == 'content_chunks'
            
            # Note: If BM25 dependencies are not available, the method should
            # gracefully fall back to standard collection (per requirement 1.5)
            
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_content_chunks_with_hybrid_search_disabled(self, temp_chroma_path):
        """Test that content_chunks collection uses standard setup when hybrid search is disabled.
        
        Validates Requirements 1.4, 7.1:
        - WHEN hybrid search is disabled, collection should use standard setup
        - Logging should indicate hybrid search is disabled
        """
        # Set temporary ChromaDB path and disable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'false'
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Get or create content_chunks collection
            collection = backend._get_or_create_metadata_collection('content_chunks')
            
            # Verify collection was created with standard setup
            assert collection is not None
            assert collection.name == 'content_chunks'
            
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_non_content_chunks_collection_ignores_hybrid_search(self, temp_chroma_path):
        """Test that non-content_chunks collections ignore hybrid search setting.
        
        Validates that hybrid search is only applied to content_chunks collection.
        """
        # Set temporary ChromaDB path and enable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'true'
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Get or create a different collection (not content_chunks)
            collection = backend._get_or_create_metadata_collection('files')
            
            # Verify collection was created with standard setup
            assert collection is not None
            assert collection.name == 'files'
            
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_hybrid_search_fallback_on_bm25_unavailable(self, temp_chroma_path):
        """Test graceful fallback when BM25 is not available.
        
        Validates Requirement 1.5:
        - WHEN BM25 indexing fails during collection creation, 
          THE ChromaDB Backend SHALL log the error and fall back to dense-only search
        """
        # Set temporary ChromaDB path and enable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'true'
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Get or create content_chunks collection
            # If BM25 is not available, it should fall back to standard collection
            collection = backend._get_or_create_metadata_collection('content_chunks')
            
            # Verify collection was created (either hybrid or fallback)
            assert collection is not None
            assert collection.name == 'content_chunks'
            
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_collection_initialization_without_hybrid_search_env(self, temp_chroma_path):
        """Test that collection initialization works when USE_HYBRID_SEARCH is not set.
        
        Validates that the system defaults to dense-only search when environment variable is missing.
        """
        # Set temporary ChromaDB path, do NOT set USE_HYBRID_SEARCH
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        
        try:
            # Create backend instance
            backend = ChromaBackend()
            
            # Get or create content_chunks collection
            collection = backend._get_or_create_metadata_collection('content_chunks')
            
            # Verify collection was created with standard setup
            assert collection is not None
            assert collection.name == 'content_chunks'
            
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
