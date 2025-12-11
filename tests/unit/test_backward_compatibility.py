"""
Backward compatibility tests for hybrid search implementation.

This test suite verifies that the hybrid search implementation maintains
backward compatibility with existing code when hybrid search is disabled.

Validates Requirements 6.1, 6.2, 6.3, 6.4, 6.5:
- 6.1: Dense-only execution when hybrid search is disabled
- 6.2: Same method signature for semantic_search
- 6.3: Same result structure with additional optional fields
- 6.4: Content type filtering works in both modes
- 6.5: Fallback to dense-only when BM25 is not configured
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.backends.chroma import ChromaBackend


class TestBackwardCompatibility:
    """Test backward compatibility safeguards for hybrid search."""
    
    @pytest.fixture
    def temp_chroma_path(self):
        """Create a temporary ChromaDB path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_chroma_backend(self, temp_chroma_path):
        """Create a ChromaBackend instance with mocked ChromaDB client."""
        with patch.dict(os.environ, {'CHROMA_DB_PATH': temp_chroma_path}):
            backend = ChromaBackend()
            
            # Mock the ChromaDB client
            mock_client = Mock()
            mock_collection = Mock()
            mock_collection.name = 'content_chunks'
            mock_collection.count.return_value = 0
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_client.get_collection.return_value = mock_collection
            mock_client.list_collections.return_value = []
            
            backend._client = mock_client
            
            yield backend
    
    def test_semantic_search_signature_unchanged(self, mock_chroma_backend):
        """Test that semantic_search maintains the same method signature.
        
        Validates Requirement 6.2:
        - WHEN the semantic_search method is called, 
          THE ChromaDB Backend SHALL accept the same parameters as the current implementation
        """
        import inspect
        
        # Get the signature of semantic_search
        sig = inspect.signature(mock_chroma_backend.semantic_search)
        params = list(sig.parameters.keys())
        
        # Verify expected parameters exist
        assert 'query_text' in params
        assert 'limit' in params
        assert 'content_type' in params
        assert 'threshold' in params
        
        # Verify default values
        assert sig.parameters['limit'].default == 5
        assert sig.parameters['content_type'].default is None
        assert sig.parameters['threshold'].default is None
        
        # Verify no unexpected required parameters were added
        required_params = [
            name for name, param in sig.parameters.items()
            if param.default == inspect.Parameter.empty and name != 'self'
        ]
        assert required_params == ['query_text']
    
    def test_dense_only_mode_when_hybrid_disabled(self, mock_chroma_backend):
        """Test that dense-only search is used when hybrid search is disabled.
        
        Validates Requirement 6.1:
        - WHEN hybrid search is disabled, 
          THE ChromaDB Backend SHALL execute the semantic_search method 
          using the existing dense-only implementation
        """
        # Ensure hybrid search is disabled
        with patch.dict(os.environ, {'USE_HYBRID_SEARCH': 'false'}):
            # Mock the embedding creation
            mock_embedding = [0.1] * 384
            
            # Mock server.utils module
            mock_utils = Mock()
            mock_utils.create_embedding.return_value = mock_embedding
            sys.modules['server.utils'] = mock_utils
            
            try:
                # Mock the dense search method
                mock_dense_results = [
                    {
                        'id': 'chunk_1',
                        'content': 'test content',
                        'metadata': {'file_id': '123'},
                        'similarity': 0.9,
                        'url': 'test.txt',
                        'chunk_number': 0,
                        'summary': 'test summary',
                        'file_id': '123'
                    }
                ]
                
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results):
                    with patch.object(mock_chroma_backend, '_perform_sparse_search') as mock_sparse:
                        with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_dense_results):
                            result = mock_chroma_backend.semantic_search("test query", limit=5)
                            
                            # Verify sparse search was NOT called
                            mock_sparse.assert_not_called()
                            
                            # Verify results were returned
                            assert len(result) == 1
                            assert result[0]['id'] == 'chunk_1'
            finally:
                # Clean up mock module
                if 'server.utils' in sys.modules:
                    del sys.modules['server.utils']
    
    def test_result_structure_includes_original_fields(self, mock_chroma_backend):
        """Test that result structure includes all original fields.
        
        Validates Requirement 6.3:
        - WHEN results are returned, 
          THE ChromaDB Backend SHALL maintain the same result structure 
          with additional optional fields for hybrid search metadata
        """
        # Mock results with all required fields
        mock_results = [
            {
                'id': 'chunk_1',
                'content': 'test content',
                'metadata': {'file_id': '123', 'url': 'test.txt', 'chunk_number': 0, 'summary': 'test'},
                'similarity': 0.9,
                'distance': 0.2,
                'url': 'test.txt',
                'chunk_number': 0,
                'summary': 'test summary',
                'file_id': '123'
            }
        ]
        
        # Apply threshold and limit (which ensures all fields are present)
        result = mock_chroma_backend._apply_threshold_and_limit(mock_results, None, 5)
        
        # Verify all original fields are present
        assert len(result) == 1
        assert 'id' in result[0]
        assert 'content' in result[0]
        assert 'metadata' in result[0]
        assert 'similarity' in result[0]
        assert 'url' in result[0]
        assert 'chunk_number' in result[0]
        assert 'summary' in result[0]
        assert 'file_id' in result[0]
        
        # Verify optional hybrid search fields are present (even if None)
        assert 'rrf_score' in result[0]
    
    def test_result_structure_in_hybrid_mode(self, mock_chroma_backend):
        """Test that result structure includes hybrid search fields when enabled.
        
        Validates Requirement 6.3:
        - WHEN results are returned in hybrid mode,
          THE ChromaDB Backend SHALL include both original fields and hybrid search metadata
        """
        # Mock results from RRF merging
        mock_results = [
            {
                'id': 'chunk_1',
                'content': 'test content',
                'metadata': {'file_id': '123'},
                'similarity': 0.9,
                'url': 'test.txt',
                'chunk_number': 0,
                'summary': 'test summary',
                'file_id': '123',
                'rrf_score': 0.032,
                'dense_rank': 1,
                'sparse_rank': 2
            }
        ]
        
        # Apply threshold and limit
        result = mock_chroma_backend._apply_threshold_and_limit(mock_results, None, 5)
        
        # Verify all original fields are present
        assert 'id' in result[0]
        assert 'content' in result[0]
        assert 'metadata' in result[0]
        assert 'similarity' in result[0]
        
        # Verify hybrid search fields are present
        assert 'rrf_score' in result[0]
        assert result[0]['rrf_score'] == 0.032
        assert 'dense_rank' in result[0]
        assert 'sparse_rank' in result[0]
    
    def test_content_type_filtering_in_dense_mode(self, mock_chroma_backend):
        """Test that content_type filtering works when hybrid search is disabled.
        
        Validates Requirement 6.4:
        - WHEN content_type filtering is specified,
          THE ChromaDB Backend SHALL apply the filter to search results
        """
        # Ensure hybrid search is disabled
        with patch.dict(os.environ, {'USE_HYBRID_SEARCH': 'false'}):
            # Mock the embedding creation
            mock_embedding = [0.1] * 384
            
            # Mock server.utils module
            mock_utils = Mock()
            mock_utils.create_embedding.return_value = mock_embedding
            sys.modules['server.utils'] = mock_utils
            
            try:
                # Mock the dense search method
                mock_dense_results = [
                    {
                        'id': 'chunk_1',
                        'content': 'test content',
                        'metadata': {'file_id': '123', 'content_type': 'documentation'},
                        'similarity': 0.9,
                        'url': 'test.txt',
                        'chunk_number': 0,
                        'summary': 'test summary',
                        'file_id': '123'
                    }
                ]
                
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results) as mock_dense:
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_dense_results):
                        result = mock_chroma_backend.semantic_search(
                            "test query", 
                            limit=5, 
                            content_type='documentation'
                        )
                        
                        # Verify dense search was called with where clause
                        mock_dense.assert_called_once()
                        call_args = mock_dense.call_args
                        where_clause = call_args[0][2]  # Third argument is where_clause
                        assert where_clause == {'content_type': 'documentation'}
            finally:
                # Clean up mock module
                if 'server.utils' in sys.modules:
                    del sys.modules['server.utils']
    
    def test_content_type_filtering_in_hybrid_mode(self, mock_chroma_backend):
        """Test that content_type filtering works in hybrid search mode.
        
        Validates Requirement 6.4:
        - WHEN content_type filtering is specified in hybrid mode,
          THE ChromaDB Backend SHALL apply the filter to both dense and sparse searches
        """
        # Enable hybrid search
        with patch.dict(os.environ, {'USE_HYBRID_SEARCH': 'true'}):
            # Mock the embedding creation
            mock_embedding = [0.1] * 384
            
            # Mock server.utils module
            mock_utils = Mock()
            mock_utils.create_embedding.return_value = mock_embedding
            sys.modules['server.utils'] = mock_utils
            
            try:
                mock_dense_results = [{'id': 'chunk_1', 'content': 'test', 'metadata': {}, 'similarity': 0.9, 'url': '', 'chunk_number': 0, 'summary': '', 'file_id': ''}]
                mock_sparse_results = [{'id': 'chunk_2', 'content': 'test', 'metadata': {}, 'bm25_score': 0.8, 'url': '', 'chunk_number': 0, 'summary': '', 'file_id': ''}]
                mock_merged_results = [{'id': 'chunk_1', 'content': 'test', 'metadata': {}, 'similarity': 0.9, 'rrf_score': 0.032, 'url': '', 'chunk_number': 0, 'summary': '', 'file_id': ''}]
                
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results) as mock_dense:
                    with patch.object(mock_chroma_backend, '_perform_sparse_search', return_value=mock_sparse_results) as mock_sparse:
                        with patch.object(mock_chroma_backend, '_merge_results_with_rrf', return_value=mock_merged_results):
                            with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_merged_results):
                                result = mock_chroma_backend.semantic_search(
                                    "test query",
                                    limit=5,
                                    content_type='source_code'
                                )
                                
                                # Verify both searches were called with where clause
                                mock_dense.assert_called_once()
                                mock_sparse.assert_called_once()
                                
                                dense_where = mock_dense.call_args[0][2]
                                sparse_where = mock_sparse.call_args[0][2]
                                
                                assert dense_where == {'content_type': 'source_code'}
                                assert sparse_where == {'content_type': 'source_code'}
            finally:
                # Clean up mock module
                if 'server.utils' in sys.modules:
                    del sys.modules['server.utils']
    
    def test_fallback_to_dense_when_bm25_not_configured(self, mock_chroma_backend):
        """Test fallback to dense-only when BM25 is not configured.
        
        Validates Requirement 6.5:
        - WHEN the collection does not have BM25 indexing configured,
          THE ChromaDB Backend SHALL fall back to dense-only search without errors
        """
        # Mock _setup_hybrid_collection to return None (BM25 not available)
        with patch.object(mock_chroma_backend, '_setup_hybrid_collection', return_value=None):
            # Mock standard collection creation
            mock_collection = Mock()
            mock_collection.name = 'content_chunks'
            mock_chroma_backend._client.get_or_create_collection.return_value = mock_collection
            
            # Enable hybrid search
            with patch.dict(os.environ, {'USE_HYBRID_SEARCH': 'true'}):
                # Get or create collection
                collection = mock_chroma_backend._get_or_create_metadata_collection('content_chunks')
                
                # Verify fallback collection was created
                assert collection is not None
                assert collection.name == 'content_chunks'
                
                # Verify standard collection creation was called (fallback)
                mock_chroma_backend._client.get_or_create_collection.assert_called()
    
    def test_empty_query_handling(self, mock_chroma_backend):
        """Test that empty queries are handled gracefully.
        
        Validates Requirement 8.1:
        - WHEN the query text is empty or whitespace-only,
          THE ChromaDB Backend SHALL return an empty result list
        """
        # Test empty string
        result = mock_chroma_backend.semantic_search("", limit=5)
        assert result == []
        
        # Test whitespace-only
        result = mock_chroma_backend.semantic_search("   ", limit=5)
        assert result == []
        
        # Test None (should handle gracefully)
        result = mock_chroma_backend.semantic_search(None, limit=5)
        assert result == []
    
    def test_invalid_limit_handling(self, mock_chroma_backend):
        """Test that invalid limit values are handled gracefully.
        
        Validates Requirement 8.4:
        - WHEN the limit parameter is less than 1,
          THE ChromaDB Backend SHALL use a default limit of 5
        """
        # Ensure hybrid search is disabled for this test
        with patch.dict(os.environ, {'USE_HYBRID_SEARCH': 'false'}):
            # Mock the embedding creation
            mock_embedding = [0.1] * 384
            
            # Mock server.utils module
            mock_utils = Mock()
            mock_utils.create_embedding.return_value = mock_embedding
            sys.modules['server.utils'] = mock_utils
            
            try:
                mock_results = []
                
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_results) as mock_dense:
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_results):
                        # Test with limit = 0
                        result = mock_chroma_backend.semantic_search("test query", limit=0)
                        
                        # Verify dense search was called with default limit of 5
                        mock_dense.assert_called_once()
                        call_args = mock_dense.call_args
                        limit_arg = call_args[0][1]  # Second argument is limit
                        assert limit_arg == 5
            finally:
                # Clean up mock module
                if 'server.utils' in sys.modules:
                    del sys.modules['server.utils']
    
    def test_backward_compatible_with_existing_code(self, mock_chroma_backend):
        """Test that existing code patterns work without modifications.
        
        This test simulates typical usage patterns from existing code to ensure
        backward compatibility.
        """
        # Ensure hybrid search is disabled (default behavior)
        with patch.dict(os.environ, {}, clear=True):
            # Remove USE_HYBRID_SEARCH if it exists
            if 'USE_HYBRID_SEARCH' in os.environ:
                del os.environ['USE_HYBRID_SEARCH']
            
            # Mock the embedding creation
            mock_embedding = [0.1] * 384
            
            # Mock server.utils module
            mock_utils = Mock()
            mock_utils.create_embedding.return_value = mock_embedding
            sys.modules['server.utils'] = mock_utils
            
            try:
                mock_results = [
                    {
                        'id': 'chunk_1',
                        'content': 'test content',
                        'metadata': {'file_id': '123'},
                        'similarity': 0.9,
                        'url': 'test.txt',
                        'chunk_number': 0,
                        'summary': 'test summary',
                        'file_id': '123'
                    }
                ]
                
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_results):
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_results):
                        # Pattern 1: Basic search
                        result = mock_chroma_backend.semantic_search("test query")
                        assert len(result) == 1
                        assert 'id' in result[0]
                        assert 'content' in result[0]
                        
                        # Pattern 2: Search with limit
                        result = mock_chroma_backend.semantic_search("test query", limit=10)
                        assert len(result) == 1
                        
                        # Pattern 3: Search with content type filter
                        result = mock_chroma_backend.semantic_search("test query", content_type='documentation')
                        assert len(result) == 1
                        
                        # Pattern 4: Search with threshold
                        result = mock_chroma_backend.semantic_search("test query", threshold=0.5)
                        assert len(result) == 1
                        
                        # Pattern 5: Search with all parameters
                        result = mock_chroma_backend.semantic_search(
                            "test query",
                            limit=10,
                            content_type='documentation',
                            threshold=0.5
                        )
                        assert len(result) == 1
            finally:
                # Clean up mock module
                if 'server.utils' in sys.modules:
                    del sys.modules['server.utils']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
