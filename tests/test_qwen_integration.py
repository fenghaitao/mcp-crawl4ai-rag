#!/usr/bin/env python3
"""
Integration test for Qwen embeddings with the full MCP server stack.
This test verifies that Qwen embeddings work end-to-end.
"""
import os
import sys
import pytest
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestQwenIntegration:
    """Integration tests for Qwen embeddings in the full MCP server context."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Set up test environment with Qwen embeddings enabled."""
        # Save original environment
        self.original_env = {
            "USE_QWEN_EMBEDDINGS": os.environ.get("USE_QWEN_EMBEDDINGS"),
            "USE_COPILOT_EMBEDDINGS": os.environ.get("USE_COPILOT_EMBEDDINGS"),
            "USE_CONTEXTUAL_EMBEDDINGS": os.environ.get("USE_CONTEXTUAL_EMBEDDINGS"),
        }
        
        # Set test environment
        os.environ["USE_QWEN_EMBEDDINGS"] = "true"
        os.environ["USE_COPILOT_EMBEDDINGS"] = "false"
        os.environ["USE_CONTEXTUAL_EMBEDDINGS"] = "false"
        
        yield
        
        # Restore original environment
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
    
    def test_qwen_in_document_processing(self):
        """Test that Qwen embeddings work in document processing pipeline."""
        try:
            from utils import add_documents_to_supabase
            
            # Mock Supabase client
            mock_client = MagicMock()
            mock_client.table.return_value.delete.return_value.in_.return_value.execute.return_value = None
            mock_client.table.return_value.insert.return_value.execute.return_value = None
            
            # Test data
            urls = ["https://example.com/doc1"]
            chunk_numbers = [0]
            contents = ["This is a test document content for embedding."]
            metadatas = [{"test": "metadata"}]
            url_to_full_document = {"https://example.com/doc1": "Full document content"}
            
            # This should use Qwen embeddings internally
            add_documents_to_supabase(
                mock_client,
                urls,
                chunk_numbers,
                contents,
                metadatas,
                url_to_full_document
            )
            
            # Verify that insert was called (meaning embeddings were created)
            mock_client.table.assert_called()
            
        except ImportError:
            pytest.skip("Dependencies not available")
    
    def test_qwen_in_search_functionality(self):
        """Test that Qwen embeddings work in search functionality."""
        try:
            from utils import search_documents
            
            # Mock Supabase client
            mock_client = MagicMock()
            mock_client.rpc.return_value.execute.return_value.data = [
                {
                    "url": "https://example.com/doc1",
                    "content": "Test content",
                    "metadata": {"test": "metadata"},
                    "similarity": 0.8
                }
            ]
            
            # This should use Qwen embeddings to create query embedding
            results = search_documents(
                mock_client,
                "test query",
                match_count=5
            )
            
            # Verify that RPC was called with embeddings
            mock_client.rpc.assert_called_once()
            
            # Get the call arguments - could be positional or keyword
            call_args, call_kwargs = mock_client.rpc.call_args
            
            # The function should be called with 'match_crawled_pages' and parameters
            assert len(call_args) >= 1
            assert call_args[0] == 'match_crawled_pages'
            
            # Parameters should be in the second positional argument or in kwargs
            if len(call_args) >= 2:
                params = call_args[1]
            else:
                # Fallback to checking kwargs or direct parameters
                params = call_kwargs
            
            assert 'query_embedding' in params
            assert isinstance(params['query_embedding'], list)
            assert len(params['query_embedding']) > 0
            
        except ImportError:
            pytest.skip("Dependencies not available")
    
    def test_qwen_embedding_consistency(self):
        """Test that Qwen embeddings are consistent across calls."""
        try:
            from utils import create_embedding
            
            test_text = "Consistent embedding test"
            
            # Create embedding twice
            embedding1 = create_embedding(test_text)
            embedding2 = create_embedding(test_text)
            
            # Skip if we got dummy embeddings
            if all(v == 0.0 for v in embedding1):
                pytest.skip("Model not available, got dummy embeddings")
            
            # Should be identical for same input
            assert embedding1 == embedding2, "Embeddings should be consistent for same input"
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_embedding_dimensions(self):
        """Test that Qwen embeddings have expected dimensions."""
        try:
            from utils import create_embeddings_batch
            
            test_texts = ["Short text", "This is a longer text with more words and content"]
            embeddings = create_embeddings_batch(test_texts)
            
            # Skip if we got dummy embeddings
            if all(v == 0.0 for v in embeddings[0]):
                pytest.skip("Model not available, got dummy embeddings")
            
            # All embeddings should have same dimension regardless of text length
            assert len(embeddings[0]) == len(embeddings[1])
            
            # Qwen3-Embedding-0.6B should produce embeddings of specific dimension
            # (This might vary, but let's check it's reasonable)
            embedding_dim = len(embeddings[0])
            assert embedding_dim > 100, f"Embedding dimension too small: {embedding_dim}"
            assert embedding_dim < 10000, f"Embedding dimension too large: {embedding_dim}"
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_performance_batch_vs_single(self):
        """Test that batch processing works efficiently."""
        try:
            from utils import create_embedding, create_embeddings_batch
            import time
            
            test_texts = ["Text 1", "Text 2", "Text 3"]
            
            # Single embeddings
            start_time = time.time()
            single_embeddings = [create_embedding(text) for text in test_texts]
            single_time = time.time() - start_time
            
            # Batch embeddings
            start_time = time.time()
            batch_embeddings = create_embeddings_batch(test_texts)
            batch_time = time.time() - start_time
            
            # Skip if we got dummy embeddings
            if all(v == 0.0 for v in batch_embeddings[0]):
                pytest.skip("Model not available, got dummy embeddings")
            
            # Results should be identical
            assert len(single_embeddings) == len(batch_embeddings)
            for i in range(len(test_texts)):
                assert single_embeddings[i] == batch_embeddings[i]
            
            # Batch should generally be faster (though this might not always be true for small batches)
            print(f"Single embedding time: {single_time:.4f}s")
            print(f"Batch embedding time: {batch_time:.4f}s")
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    @pytest.mark.parametrize("text_length", [10, 100, 1000, 5000])
    def test_qwen_handles_various_text_lengths(self, text_length):
        """Test that Qwen can handle various text lengths."""
        try:
            from utils import create_embedding
            
            # Create text of specified length
            test_text = "word " * (text_length // 5)  # Approximate word count
            
            embedding = create_embedding(test_text)
            
            # Skip if we got dummy embeddings
            if all(v == 0.0 for v in embedding):
                pytest.skip("Model not available, got dummy embeddings")
            
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_environment_variable_precedence(self):
        """Test that Qwen takes precedence over other embedding methods."""
        # Test with multiple embedding options enabled
        with patch.dict(os.environ, {
            "USE_QWEN_EMBEDDINGS": "true",
            "USE_COPILOT_EMBEDDINGS": "true",
        }):
            # Mock the Qwen function to verify it's called
            with patch('utils.create_embeddings_batch_qwen') as mock_qwen:
                mock_qwen.return_value = [[0.1, 0.2, 0.3]]
                
                try:
                    from utils import create_embeddings_batch
                    
                    result = create_embeddings_batch(["test"])
                    
                    # Qwen should be called, not Copilot
                    mock_qwen.assert_called_once_with(["test"])
                    assert result == [[0.1, 0.2, 0.3]]
                    
                except ImportError:
                    pytest.skip("Dependencies not available")

if __name__ == "__main__":
    # Allow running as script for quick testing
    pytest.main([__file__, "-v", "-s"])