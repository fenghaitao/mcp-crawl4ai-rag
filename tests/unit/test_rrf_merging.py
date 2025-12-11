"""
Unit tests for RRF merging algorithm.
"""

import pytest
from unittest.mock import Mock


class TestRRFMerging:
    """Test suite for _merge_results_with_rrf method."""
    
    @pytest.fixture
    def mock_chroma_backend(self):
        """Create mock ChromaDB backend."""
        from core.backends.chroma import ChromaBackend
        
        backend = ChromaBackend.__new__(ChromaBackend)
        backend._client = Mock()
        return backend
    
    def test_merge_results_with_rrf_combines_scores(self, mock_chroma_backend):
        """Test that RRF correctly combines scores from both methods."""
        dense_results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.8},
        ]
        
        sparse_results = [
            {'id': 'doc1', 'content': 'Content 1', 'bm25_score': 0.7},
            {'id': 'doc3', 'content': 'Content 3', 'bm25_score': 0.6},
        ]
        
        k = 60
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results, k)
        
        # Verify doc1 appears in both and has combined score
        doc1 = next(r for r in merged if r['id'] == 'doc1')
        assert doc1['dense_rank'] == 1
        assert doc1['sparse_rank'] == 1
        # RRF score should be: 1/(60+1) + 1/(60+1) = 2/61
        expected_rrf = (1 / (k + 1)) + (1 / (k + 1))
        assert abs(doc1['rrf_score'] - expected_rrf) < 0.0001
        
        # Verify doc2 only in dense
        doc2 = next(r for r in merged if r['id'] == 'doc2')
        assert doc2['dense_rank'] == 2
        assert doc2['sparse_rank'] is None
        expected_rrf = 1 / (k + 2)
        assert abs(doc2['rrf_score'] - expected_rrf) < 0.0001
        
        # Verify doc3 only in sparse
        doc3 = next(r for r in merged if r['id'] == 'doc3')
        assert doc3['dense_rank'] is None
        assert doc3['sparse_rank'] == 2
        expected_rrf = 1 / (k + 2)
        assert abs(doc3['rrf_score'] - expected_rrf) < 0.0001
    
    def test_merge_results_sorted_by_rrf_score(self, mock_chroma_backend):
        """Test that merged results are sorted by RRF score descending."""
        dense_results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.8},
            {'id': 'doc3', 'content': 'Content 3', 'similarity': 0.7},
        ]
        
        sparse_results = [
            {'id': 'doc3', 'content': 'Content 3', 'bm25_score': 0.9},
            {'id': 'doc1', 'content': 'Content 1', 'bm25_score': 0.8},
            {'id': 'doc4', 'content': 'Content 4', 'bm25_score': 0.7},
        ]
        
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results)
        
        # Verify results are sorted by RRF score
        for i in range(len(merged) - 1):
            assert merged[i]['rrf_score'] >= merged[i + 1]['rrf_score']
        
        # doc1 and doc3 should rank higher (appear in both)
        assert merged[0]['id'] in ['doc1', 'doc3']
        assert merged[1]['id'] in ['doc1', 'doc3']
    
    def test_merge_results_with_empty_dense(self, mock_chroma_backend):
        """Test merging with empty dense results."""
        dense_results = []
        sparse_results = [
            {'id': 'doc1', 'content': 'Content 1', 'bm25_score': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'bm25_score': 0.8},
        ]
        
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results)
        
        assert len(merged) == 2
        assert all(r['dense_rank'] is None for r in merged)
        assert all(r['sparse_rank'] is not None for r in merged)
    
    def test_merge_results_with_empty_sparse(self, mock_chroma_backend):
        """Test merging with empty sparse results."""
        dense_results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
            {'id': 'doc2', 'content': 'Content 2', 'similarity': 0.8},
        ]
        sparse_results = []
        
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results)
        
        assert len(merged) == 2
        assert all(r['dense_rank'] is not None for r in merged)
        assert all(r['sparse_rank'] is None for r in merged)
    
    def test_merge_results_with_custom_k(self, mock_chroma_backend):
        """Test RRF with custom k parameter."""
        dense_results = [
            {'id': 'doc1', 'content': 'Content 1', 'similarity': 0.9},
        ]
        sparse_results = [
            {'id': 'doc1', 'content': 'Content 1', 'bm25_score': 0.9},
        ]
        
        k = 100
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results, k)
        
        # Verify custom k is used
        expected_rrf = (1 / (k + 1)) + (1 / (k + 1))
        assert abs(merged[0]['rrf_score'] - expected_rrf) < 0.0001
    
    def test_merge_results_preserves_metadata(self, mock_chroma_backend):
        """Test that merging preserves all metadata from results."""
        dense_results = [
            {
                'id': 'doc1',
                'content': 'Content 1',
                'similarity': 0.9,
                'metadata': {'url': 'http://example.com', 'chunk_number': 0},
                'url': 'http://example.com',
                'chunk_number': 0,
                'summary': 'Summary 1',
                'file_id': 'file1'
            },
        ]
        sparse_results = []
        
        merged = mock_chroma_backend._merge_results_with_rrf(dense_results, sparse_results)
        
        # Verify all fields are preserved
        assert merged[0]['content'] == 'Content 1'
        assert merged[0]['similarity'] == 0.9
        assert merged[0]['metadata']['url'] == 'http://example.com'
        assert merged[0]['url'] == 'http://example.com'
        assert merged[0]['summary'] == 'Summary 1'
