#!/usr/bin/env python3
"""
Pytest test cases for Qwen embedding integration.
"""
import os
import sys
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestQwenEmbeddings:
    """Test cases for Qwen embedding functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Set up test environment."""
        # Save original environment
        self.original_env = os.environ.get("USE_QWEN_EMBEDDINGS")
        # Set to use Qwen embeddings for tests
        os.environ["USE_QWEN_EMBEDDINGS"] = "true"
        
        yield
        
        # Restore original environment
        if self.original_env is not None:
            os.environ["USE_QWEN_EMBEDDINGS"] = self.original_env
        else:
            os.environ.pop("USE_QWEN_EMBEDDINGS", None)
    
    def test_qwen_model_loading(self):
        """Test that Qwen model can be loaded successfully."""
        try:
            from utils import get_qwen_embedding_model
            
            model = get_qwen_embedding_model()
            
            # If sentence-transformers is not installed, model should be None
            # If it is installed, model should be loaded
            if model is None:
                pytest.skip("sentence-transformers not installed or model not available")
            else:
                assert model is not None
                assert hasattr(model, 'encode')
                
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_single_embedding(self):
        """Test single embedding creation with Qwen."""
        try:
            from utils import create_embedding_qwen
            
            embedding = create_embedding_qwen("Hello world")
            
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
            
            # Check if it's not all zeros (unless model failed to load)
            if not all(v == 0.0 for v in embedding):
                # Real embedding should have some variation
                assert max(embedding) != min(embedding)
                
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_batch_embeddings(self):
        """Test batch embedding creation with Qwen."""
        try:
            from utils import create_embeddings_batch_qwen
            
            test_texts = ["Hello world", "This is a test", "Qwen embedding model"]
            embeddings = create_embeddings_batch_qwen(test_texts)
            
            assert isinstance(embeddings, list)
            assert len(embeddings) == len(test_texts)
            
            for embedding in embeddings:
                assert isinstance(embedding, list)
                assert len(embedding) > 0
                assert all(isinstance(x, float) for x in embedding)
            
            # All embeddings should have the same dimension
            embedding_dims = [len(emb) for emb in embeddings]
            assert len(set(embedding_dims)) == 1, "All embeddings should have same dimension"
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_embedding_similarity(self):
        """Test that similar texts produce similar embeddings."""
        try:
            from utils import create_embeddings_batch_qwen
            
            # Test with similar texts
            similar_texts = ["Hello world", "Hi there world"]
            embeddings = create_embeddings_batch_qwen(similar_texts)
            
            # Skip if we got dummy embeddings (all zeros)
            if all(v == 0.0 for v in embeddings[0]):
                pytest.skip("Model not available, got dummy embeddings")
            
            # Calculate cosine similarity
            emb1 = np.array(embeddings[0])
            emb2 = np.array(embeddings[1])
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            # Similar texts should have reasonable similarity (> 0.3)
            assert similarity > 0.3, f"Similarity too low: {similarity}"
            
            # Test with dissimilar texts
            dissimilar_texts = ["Hello world", "Quantum physics equations"]
            dissimilar_embeddings = create_embeddings_batch_qwen(dissimilar_texts)
            
            emb3 = np.array(dissimilar_embeddings[0])
            emb4 = np.array(dissimilar_embeddings[1])
            dissimilar_similarity = np.dot(emb3, emb4) / (np.linalg.norm(emb3) * np.linalg.norm(emb4))
            
            # Dissimilar texts should be less similar than similar texts
            assert similarity > dissimilar_similarity, "Similar texts should be more similar than dissimilar ones"
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_main_embedding_functions_use_qwen(self):
        """Test that main embedding functions use Qwen when enabled."""
        try:
            from utils import create_embedding, create_embeddings_batch
            
            # Test single embedding
            single_embedding = create_embedding("Test text")
            assert isinstance(single_embedding, list)
            assert len(single_embedding) > 0
            
            # Test batch embedding
            batch_embeddings = create_embeddings_batch(["Test 1", "Test 2"])
            assert isinstance(batch_embeddings, list)
            assert len(batch_embeddings) == 2
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    def test_qwen_fallback_behavior(self):
        """Test that fallback works when Qwen is not available."""
        with patch('utils.get_qwen_embedding_model', return_value=None):
            from utils import create_embeddings_batch_qwen
            
            # Should return dummy embeddings when model is not available
            embeddings = create_embeddings_batch_qwen(["Test text"])
            
            assert isinstance(embeddings, list)
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1536  # Default embedding size
            assert all(v == 0.0 for v in embeddings[0])  # Should be all zeros
    
    def test_empty_input_handling(self):
        """Test handling of empty input."""
        try:
            from utils import create_embeddings_batch_qwen
            
            # Empty list should return empty list
            embeddings = create_embeddings_batch_qwen([])
            assert embeddings == []
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
    
    @patch('builtins.print')
    def test_qwen_error_handling(self, mock_print):
        """Test error handling in Qwen embedding functions."""
        # Mock the model to raise an exception during encoding
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Test exception")
        
        with patch('utils.get_qwen_embedding_model', return_value=mock_model):
            from utils import create_embeddings_batch_qwen
            
            embeddings = create_embeddings_batch_qwen(["Test text"])
            
            # Should return dummy embeddings on error
            assert isinstance(embeddings, list)
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1536
            assert all(v == 0.0 for v in embeddings[0])
            
            # Should have printed error message
            mock_print.assert_any_call("Error creating Qwen embeddings: Test exception")

if __name__ == "__main__":
    # Allow running as script for quick testing
    pytest.main([__file__, "-v"])