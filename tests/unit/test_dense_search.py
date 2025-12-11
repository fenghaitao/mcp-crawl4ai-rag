"""
Unit tests for dense search method.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestDenseSearch:
    """Test suite for _perform_dense_search method."""
    
    @pytest.fixture
    def mock_chroma_backend(self):
        """Create mock ChromaDB backend."""
        from core.backends.chroma import ChromaBackend
        
        backend = ChromaBackend.__new__(ChromaBackend)
        backend._client = Mock()
        return backend
    
    def test_perform_dense_search_returns_results(self, mock_chroma_backend):
        """Test that _perform_dense_search returns formatted results."""
        # Mock the collection and query results
        mock_collection = Mock()
        mock_chroma_backend._client.get_collection.return_value = mock_collection
        
        # Mock query results
        mock_collection.query.return_value = {
            'ids': [['chunk1', 'chunk2']],
            'documents': [['Document 1 content', 'Document 2 content']],
            'metadatas': [[
                {
                    'url': 'http://example.com/doc1',
                    'chunk_number': 0,
                    'summary': 'Summary 1',
                    'file_id': 'file1'
                },
                {
                    'url': 'http://example.com/doc2',
                    'chunk_number': 1,
                    'summary': 'Summary 2',
                    'file_id': 'file2'
                }
            ]],
            'distances': [[0.2, 0.4]]
        }
        
        # Test query embedding
        query_embedding = [0.1] * 768
        limit = 5
        where_clause = None
        
        results = mock_chroma_backend._perform_dense_search(query_embedding, limit, where_clause)
        
        # Verify results
        assert len(results) == 2
        assert results[0]['id'] == 'chunk1'
        assert results[0]['content'] == 'Document 1 content'
        assert results[0]['url'] == 'http://example.com/doc1'
        assert 'similarity' in results[0]
        assert 'distance' in results[0]
        
        # Verify collection.query was called with correct parameters
        mock_collection.query.assert_called_once_with(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_clause
        )
    
    def test_perform_dense_search_with_where_clause(self, mock_chroma_backend):
        """Test that _perform_dense_search applies where clause filter."""
        # Mock the collection and query results
        mock_collection = Mock()
        mock_chroma_backend._client.get_collection.return_value = mock_collection
        
        # Mock query results
        mock_collection.query.return_value = {
            'ids': [['chunk1']],
            'documents': [['Document 1 content']],
            'metadatas': [[
                {
                    'url': 'http://example.com/doc1',
                    'chunk_number': 0,
                    'summary': 'Summary 1',
                    'file_id': 'file1',
                    'content_type': 'documentation'
                }
            ]],
            'distances': [[0.2]]
        }
        
        # Test with where clause
        query_embedding = [0.1] * 768
        limit = 5
        where_clause = {"content_type": "documentation"}
        
        results = mock_chroma_backend._perform_dense_search(query_embedding, limit, where_clause)
        
        # Verify where clause was passed
        mock_collection.query.assert_called_once_with(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_clause
        )
        
        assert len(results) == 1
        assert results[0]['metadata']['content_type'] == 'documentation'
    
    def test_perform_dense_search_handles_empty_results(self, mock_chroma_backend):
        """Test that _perform_dense_search handles empty results gracefully."""
        # Mock the collection and query results
        mock_collection = Mock()
        mock_chroma_backend._client.get_collection.return_value = mock_collection
        
        # Mock empty query results
        mock_collection.query.return_value = {
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        
        query_embedding = [0.1] * 768
        limit = 5
        where_clause = None
        
        results = mock_chroma_backend._perform_dense_search(query_embedding, limit, where_clause)
        
        # Verify empty results
        assert len(results) == 0
    
    def test_perform_dense_search_raises_on_error(self, mock_chroma_backend):
        """Test that _perform_dense_search raises exception on error."""
        # Mock the collection to raise an error
        mock_chroma_backend._client.get_collection.side_effect = Exception("Collection not found")
        
        query_embedding = [0.1] * 768
        limit = 5
        where_clause = None
        
        # Verify exception is raised
        with pytest.raises(Exception, match="Collection not found"):
            mock_chroma_backend._perform_dense_search(query_embedding, limit, where_clause)
    
    def test_perform_dense_search_calculates_similarity_correctly(self, mock_chroma_backend):
        """Test that similarity is calculated correctly from distance."""
        # Mock the collection and query results
        mock_collection = Mock()
        mock_chroma_backend._client.get_collection.return_value = mock_collection
        
        # Mock query results with known distance
        mock_collection.query.return_value = {
            'ids': [['chunk1']],
            'documents': [['Document 1 content']],
            'metadatas': [[
                {
                    'url': 'http://example.com/doc1',
                    'chunk_number': 0,
                    'summary': 'Summary 1',
                    'file_id': 'file1'
                }
            ]],
            'distances': [[0.5]]  # Known distance
        }
        
        query_embedding = [0.1] * 768
        limit = 5
        where_clause = None
        
        results = mock_chroma_backend._perform_dense_search(query_embedding, limit, where_clause)
        
        # Verify similarity calculation: similarity = 1 - (distance / 2)
        expected_similarity = 1 - (0.5 / 2)
        assert results[0]['similarity'] == expected_similarity
        assert results[0]['distance'] == 0.5
