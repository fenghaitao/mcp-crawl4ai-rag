"""
Unit tests for semantic_search method with hybrid search support.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock


class TestSemanticSearchHybrid:
    """Test suite for semantic_search method with hybrid search."""
    
    @pytest.fixture
    def mock_chroma_backend(self):
        """Create mock ChromaDB backend."""
        from core.backends.chroma import ChromaBackend
        
        backend = ChromaBackend.__new__(ChromaBackend)
        backend._client = Mock()
        return backend
    
    def test_empty_query_returns_empty_list(self, mock_chroma_backend):
        """Test that empty query returns empty list."""
        result = mock_chroma_backend.semantic_search("")
        assert result == []
        
        result = mock_chroma_backend.semantic_search("   ")
        assert result == []
    
    def test_invalid_limit_uses_default(self, mock_chroma_backend):
        """Test that invalid limit uses default value."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=False):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=[]):
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=[]) as mock_apply:
                        mock_chroma_backend.semantic_search("test", limit=0)
                        
                        # Should use default limit of 5
                        mock_apply.assert_called_once()
                        assert mock_apply.call_args[0][2] == 5  # limit parameter
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_dense_only_mode_when_hybrid_disabled(self, mock_chroma_backend):
        """Test that dense-only search is used when hybrid is disabled."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            mock_dense_results = [
                {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9}
            ]
            
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=False):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results):
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_dense_results) as mock_apply:
                        result = mock_chroma_backend.semantic_search("test query", limit=5)
                        
                        # Verify dense search was called
                        mock_utils.create_embedding.assert_called_once_with("test query")
                        mock_apply.assert_called_once()
                        assert result == mock_dense_results
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_hybrid_mode_performs_both_searches(self, mock_chroma_backend):
        """Test that hybrid mode performs both dense and sparse searches."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            mock_dense_results = [
                {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9}
            ]
            mock_sparse_results = [
                {'id': 'doc2', 'content': 'Content 2', 'bm25_score': 0.8}
            ]
            mock_merged_results = [
                {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9, 'rrf_score': 0.02}
            ]
            
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=True):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results):
                    with patch.object(mock_chroma_backend, '_perform_sparse_search', return_value=mock_sparse_results):
                        with patch.object(mock_chroma_backend, '_merge_results_with_rrf', return_value=mock_merged_results):
                            with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_merged_results):
                                result = mock_chroma_backend.semantic_search("test query", limit=5)
                                
                                # Verify both searches were called with 2x limit
                                mock_chroma_backend._perform_dense_search.assert_called_once()
                                mock_chroma_backend._perform_sparse_search.assert_called_once()
                                mock_chroma_backend._merge_results_with_rrf.assert_called_once()
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_hybrid_mode_handles_dense_failure(self, mock_chroma_backend):
        """Test graceful degradation when dense search fails."""
        # Mock server.utils module with embedding failure
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=None)
        sys.modules['server.utils'] = mock_utils
        
        try:
            mock_sparse_results = [
                {'id': 'doc1', 'content': 'Content 1', 'bm25_score': 0.8}
            ]
            
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=True):
                with patch.object(mock_chroma_backend, '_perform_sparse_search', return_value=mock_sparse_results):
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_sparse_results) as mock_apply:
                        result = mock_chroma_backend.semantic_search("test query", limit=5)
                        
                        # Should return sparse-only results
                        mock_apply.assert_called_once()
                        assert result == mock_sparse_results
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_hybrid_mode_handles_sparse_failure(self, mock_chroma_backend):
        """Test graceful degradation when sparse search fails."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            mock_dense_results = [
                {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9}
            ]
            
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=True):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_dense_results):
                    with patch.object(mock_chroma_backend, '_perform_sparse_search', side_effect=Exception("Sparse search failed")):
                        with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_dense_results) as mock_apply:
                            result = mock_chroma_backend.semantic_search("test query", limit=5)
                            
                            # Should return dense-only results
                            mock_apply.assert_called_once()
                            assert result == mock_dense_results
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_hybrid_mode_handles_both_failures(self, mock_chroma_backend):
        """Test that both search failures returns empty list."""
        # Mock server.utils module with embedding failure
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=None)
        sys.modules['server.utils'] = mock_utils
        
        try:
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=True):
                with patch.object(mock_chroma_backend, '_perform_sparse_search', side_effect=Exception("Sparse search failed")):
                    result = mock_chroma_backend.semantic_search("test query", limit=5)
                    
                    # Should return empty list
                    assert result == []
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_content_type_filter_applied(self, mock_chroma_backend):
        """Test that content_type filter is applied to searches."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=False):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=[]) as mock_dense:
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=[]):
                        mock_chroma_backend.semantic_search("test", content_type="documentation")
                        
                        # Verify where clause was passed
                        call_args = mock_dense.call_args
                        where_clause = call_args[0][2]  # Third argument
                        assert where_clause == {"content_type": "documentation"}
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
    
    def test_threshold_applied_to_results(self, mock_chroma_backend):
        """Test that threshold is applied to filter results."""
        # Mock server.utils module
        mock_utils = Mock()
        mock_utils.create_embedding = Mock(return_value=[0.1] * 768)
        sys.modules['server.utils'] = mock_utils
        
        try:
            mock_results = [
                {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9}
            ]
            
            with patch.object(mock_chroma_backend, '_is_hybrid_search_enabled', return_value=False):
                with patch.object(mock_chroma_backend, '_perform_dense_search', return_value=mock_results):
                    with patch.object(mock_chroma_backend, '_apply_threshold_and_limit', return_value=mock_results) as mock_apply:
                        mock_chroma_backend.semantic_search("test", threshold=0.7)
                        
                        # Verify threshold was passed
                        call_args = mock_apply.call_args
                        threshold = call_args[0][1]  # Second argument
                        assert threshold == 0.7
        finally:
            if 'server.utils' in sys.modules:
                del sys.modules['server.utils']
