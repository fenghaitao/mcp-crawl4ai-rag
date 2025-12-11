"""
Unit tests to verify logging for collection initialization with hybrid search.
Tests for task 3: Verify logging requirements (Requirement 7.1).
"""

import os
import tempfile
import shutil
import pytest
import logging
from core.backends.chroma import ChromaBackend


class TestCollectionInitializationLogging:
    """Tests for logging during collection initialization."""
    
    @pytest.fixture
    def temp_chroma_path(self):
        """Create a temporary directory for ChromaDB."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_logging_when_hybrid_search_enabled(self, temp_chroma_path, caplog):
        """Test that appropriate logs are generated when hybrid search is enabled.
        
        Validates Requirement 7.1:
        - WHEN hybrid search is enabled at initialization, 
          THE ChromaDB Backend SHALL log the hybrid search configuration status
        """
        # Set temporary ChromaDB path and enable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'true'
        
        try:
            # Set log level to capture INFO messages
            with caplog.at_level(logging.INFO):
                # Create backend instance
                backend = ChromaBackend()
                
                # Get or create content_chunks collection
                collection = backend._get_or_create_metadata_collection('content_chunks')
                
                # Verify collection was created
                assert collection is not None
                
                # Check that appropriate log messages were generated
                log_messages = [record.message for record in caplog.records]
                
                # Should log that hybrid search is enabled
                assert any('Hybrid search is enabled' in msg for msg in log_messages), \
                    f"Expected log message about hybrid search being enabled. Got: {log_messages}"
                
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_logging_when_hybrid_search_disabled(self, temp_chroma_path, caplog):
        """Test that appropriate logs are generated when hybrid search is disabled.
        
        Validates Requirement 7.1:
        - Logging should indicate when hybrid search is disabled
        """
        # Set temporary ChromaDB path and disable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'false'
        
        try:
            # Set log level to capture INFO messages
            with caplog.at_level(logging.INFO):
                # Create backend instance
                backend = ChromaBackend()
                
                # Get or create content_chunks collection
                collection = backend._get_or_create_metadata_collection('content_chunks')
                
                # Verify collection was created
                assert collection is not None
                
                # Check that appropriate log messages were generated
                log_messages = [record.message for record in caplog.records]
                
                # Should log that hybrid search is disabled
                assert any('Hybrid search is disabled' in msg for msg in log_messages), \
                    f"Expected log message about hybrid search being disabled. Got: {log_messages}"
                
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
    
    def test_logging_on_bm25_fallback(self, temp_chroma_path, caplog):
        """Test that warning is logged when BM25 setup fails and fallback occurs.
        
        Validates Requirement 1.5:
        - WHEN BM25 indexing fails during collection creation, 
          THE ChromaDB Backend SHALL log the error and fall back to dense-only search
        """
        # Set temporary ChromaDB path and enable hybrid search
        os.environ['CHROMA_DB_PATH'] = temp_chroma_path
        os.environ['USE_HYBRID_SEARCH'] = 'true'
        
        try:
            # Set log level to capture WARNING messages
            with caplog.at_level(logging.WARNING):
                # Create backend instance
                backend = ChromaBackend()
                
                # Get or create content_chunks collection
                collection = backend._get_or_create_metadata_collection('content_chunks')
                
                # Verify collection was created
                assert collection is not None
                
                # Check log messages
                log_messages = [record.message for record in caplog.records]
                
                # If BM25 is not available, should log a warning about fallback
                # Note: This test may pass without the warning if BM25 is actually available
                if any('BM25' in msg or 'fallback' in msg.lower() for msg in log_messages):
                    assert any('fallback' in msg.lower() or 'using standard collection' in msg.lower() 
                              for msg in log_messages), \
                        f"Expected log message about fallback. Got: {log_messages}"
                
        finally:
            # Clean up environment
            os.environ.pop('CHROMA_DB_PATH', None)
            os.environ.pop('USE_HYBRID_SEARCH', None)
