"""
Unit tests for result filtering and limiting.
"""

import pytest
from unittest.mock import Mock


class TestResultFiltering:
    """Test suite for _apply_threshold_and_limit method."""
    
    @pytest.fixture
    def mock_chroma_backend(self):
        """Create mock ChromaDB backend."""
        from core.backends.chroma import ChromaBackend
        
        backend = ChromaBackend.__new__(ChromaBackend)
        backend._client = Mock()
        return backend
    
    def test_apply_limit_enforces_maximum(self, mock_chroma_backend):
        """Test that limit parameter is enforced."""
        results = [
            {'id': f'doc{i}', 'content': f'Content {i}', 'similarity': 0.9 - i * 0.1}
            for i in range(10)
        ]
        
        limit = 5
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, None, limit)
        
        assert len(filtered) == limit
        assert filtered[0]['id'] == 'doc0'
        assert filtered[4]['id'] == 'doc4'
    
    def test_apply_threshold_filters_results(self, mock_chroma_backend):
        """Test that threshold filtering works correctly."""
        results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.7},
            {'id': 'doc3', 'content': 'Content 3', 'similarity': 0.5},
            {'id': 'doc4', 'content': 'Content 4', 'similarity': 0.3},
        ]
        
        threshold = 0.6
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, threshold, limit)
        
        # Only doc1 and doc2 should pass threshold
        assert len(filtered) == 2
        assert all(r['similarity'] >= threshold for r in filtered)
        assert filtered[0]['id'] == 'doc1'
        assert filtered[1]['id'] == 'doc2'
    
    def test_apply_threshold_and_limit_together(self, mock_chroma_backend):
        """Test that threshold and limit work together."""
        results = [
            {'id': f'doc{i}', 'content': f'Content {i}', 'similarity': 0.9 - i * 0.1}
            for i in range(10)
        ]
        
        threshold = 0.5
        limit = 3
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, threshold, limit)
        
        # Should have at most 3 results, all above threshold
        assert len(filtered) <= limit
        assert all(r['similarity'] >= threshold for r in filtered)
    
    def test_apply_no_threshold_no_filtering(self, mock_chroma_backend):
        """Test that None threshold doesn't filter."""
        results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.1},
        ]
        
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, None, limit)
        
        assert len(filtered) == 2
    
    def test_ensures_required_fields_present(self, mock_chroma_backend):
        """Test that required fields are added if missing."""
        results = [
            {'id': 'doc1', 'content': 'Content 1'},  # Missing similarity and rrf_score
        ]
        
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, None, limit)
        
        assert 'similarity' in filtered[0]
        assert 'rrf_score' in filtered[0]
        assert filtered[0]['similarity'] == 0.0
        assert filtered[0]['rrf_score'] is None
    
    def test_preserves_existing_fields(self, mock_chroma_backend):
        """Test that existing fields are preserved."""
        results = [
            {
                'id': 'doc1',
                'content': 'Content 1',
                'similarity': 0.9,
                'rrf_score': 0.05,
                'metadata': {'url': 'http://example.com'},
                'url': 'http://example.com'
            },
        ]
        
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, None, limit)
        
        assert filtered[0]['similarity'] == 0.9
        assert filtered[0]['rrf_score'] == 0.05
        assert filtered[0]['metadata']['url'] == 'http://example.com'
    
    def test_empty_results_returns_empty(self, mock_chroma_backend):
        """Test that empty input returns empty output."""
        results = []
        
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, None, limit)
        
        assert len(filtered) == 0
    
    def test_threshold_filters_all_results(self, mock_chroma_backend):
        """Test that high threshold can filter all results."""
        results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.5},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.4},
        ]
        
        threshold = 0.9
        limit = 10
        filtered = mock_chroma_backend._apply_threshold_and_limit(results, threshold, limit)
        
        assert len(filtered) == 0
