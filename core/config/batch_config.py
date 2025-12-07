"""
Configuration management for batch processing system.
"""

from dataclasses import dataclass
from typing import Tuple
import os


@dataclass
class BatchConfig:
    """Configuration for batch processing operations."""
    
    # File size limits
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    warn_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Processing limits
    max_batch_size: int = 1000
    progress_save_interval: int = 10  # Save progress every N files
    memory_threshold_mb: int = 1024   # Warning threshold for memory usage
    
    # File format support
    supported_extensions: Tuple[str, ...] = (
        '.md', '.html', '.htm', '.rst', '.txt', '.dml', '.py',
        '.json', '.yaml', '.yml'
    )
    
    # Retry configuration
    max_retry_attempts: int = 3
    retry_backoff_factor: float = 2.0
    
    # Performance tuning
    chunk_processing_size: int = 100  # Process files in chunks
    temporal_query_limit: int = 1000  # Max versions to fetch for temporal queries
    
    @classmethod
    def from_environment(cls) -> 'BatchConfig':
        """Create configuration from environment variables."""
        return cls(
            max_file_size=int(os.getenv('BATCH_MAX_FILE_SIZE', cls.max_file_size)),
            max_batch_size=int(os.getenv('BATCH_MAX_BATCH_SIZE', cls.max_batch_size)),
            progress_save_interval=int(os.getenv('BATCH_PROGRESS_INTERVAL', cls.progress_save_interval)),
            memory_threshold_mb=int(os.getenv('BATCH_MEMORY_THRESHOLD_MB', cls.memory_threshold_mb)),
            max_retry_attempts=int(os.getenv('BATCH_MAX_RETRIES', cls.max_retry_attempts)),
            chunk_processing_size=int(os.getenv('BATCH_CHUNK_SIZE', cls.chunk_processing_size)),
            temporal_query_limit=int(os.getenv('TEMPORAL_QUERY_LIMIT', cls.temporal_query_limit))
        )


# Global configuration instance
config = BatchConfig.from_environment()