"""
Tests for batch configuration management.
"""

import os
import pytest
from core.config.batch_config import BatchConfig


class TestBatchConfig:
    """Test batch configuration functionality."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = BatchConfig()
        
        assert config.max_file_size == 50 * 1024 * 1024  # 50MB
        assert config.warn_file_size == 10 * 1024 * 1024  # 10MB
        assert config.max_batch_size == 1000
        assert config.progress_save_interval == 10
        assert config.max_retry_attempts == 3
        assert config.chunk_processing_size == 100
        assert '.md' in config.supported_extensions
        assert '.py' in config.supported_extensions
    
    def test_environment_configuration(self):
        """Test configuration from environment variables."""
        # Set environment variables
        env_vars = {
            'BATCH_MAX_FILE_SIZE': '100000000',  # 100MB
            'BATCH_MAX_BATCH_SIZE': '2000',
            'BATCH_PROGRESS_INTERVAL': '5',
            'BATCH_MEMORY_THRESHOLD_MB': '2048',
            'BATCH_MAX_RETRIES': '5',
            'BATCH_CHUNK_SIZE': '50'
        }
        
        # Mock environment
        for key, value in env_vars.items():
            os.environ[key] = value
        
        try:
            config = BatchConfig.from_environment()
            
            assert config.max_file_size == 100000000
            assert config.max_batch_size == 2000
            assert config.progress_save_interval == 5
            assert config.memory_threshold_mb == 2048
            assert config.max_retry_attempts == 5
            assert config.chunk_processing_size == 50
            
        finally:
            # Clean up environment
            for key in env_vars.keys():
                os.environ.pop(key, None)
    
    def test_supported_extensions(self):
        """Test supported file extensions."""
        config = BatchConfig()
        
        # Test common extensions are supported
        expected_extensions = ['.md', '.html', '.htm', '.rst', '.txt', '.dml', '.py']
        for ext in expected_extensions:
            assert ext in config.supported_extensions
        
        # Test case sensitivity
        assert '.MD' not in config.supported_extensions  # Should be lowercase
    
    def test_configuration_validation(self):
        """Test configuration value validation."""
        config = BatchConfig()
        
        # Test positive values
        assert config.max_file_size > 0
        assert config.max_batch_size > 0
        assert config.progress_save_interval > 0
        assert config.max_retry_attempts >= 1
        assert config.retry_backoff_factor > 0