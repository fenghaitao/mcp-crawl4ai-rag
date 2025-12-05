"""
Configuration management for user manual chunker.

Provides centralized configuration with environment variable support
and sensible defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ChunkerConfig:
    """Configuration for the user manual chunking pipeline."""
    
    # Chunking parameters
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    chunk_overlap: int = 50
    size_metric: Literal["characters", "tokens"] = "characters"
    
    # Model configuration
    embedding_model: str = "text-embedding-3-small"
    summary_model: str = "iflow/qwen3-coder-plus"
    
    # Embedding provider selection (aligned with .env)
    use_qwen_embeddings: bool = False
    use_copilot_embeddings: bool = True
    
    # Processing options
    generate_summaries: bool = True
    generate_embeddings: bool = True
    use_contextual_embeddings: bool = True
    
    # Batch processing
    embedding_batch_size: int = 32
    
    # Summary configuration
    max_summary_length: int = 150
    summary_timeout_seconds: int = 30
    
    # Rate limiting (aligned with .env)
    copilot_requests_per_minute: int = 60
    
    # Error handling
    embedding_retry_attempts: int = 3
    embedding_retry_backoff: float = 2.0  # Exponential backoff multiplier
    
    @classmethod
    def from_env(cls) -> 'ChunkerConfig':
        """
        Create configuration from environment variables.
        
        Environment variables:
            MANUAL_MAX_CHUNK_SIZE: Maximum chunk size (default: 1000)
            MANUAL_MIN_CHUNK_SIZE: Minimum chunk size (default: 100)
            MANUAL_CHUNK_OVERLAP: Chunk overlap size (default: 50)
            MANUAL_SIZE_METRIC: Size metric - 'characters' or 'tokens' (default: characters)
            MANUAL_EMBEDDING_MODEL: Embedding model name (default: text-embedding-3-small)
            MANUAL_SUMMARY_MODEL: Summary model name (default: iflow/qwen3-coder-plus)
            MANUAL_GENERATE_SUMMARIES: Generate summaries (default: true)
            MANUAL_GENERATE_EMBEDDINGS: Generate embeddings (default: true)
            
            # Embedding provider selection (from .env)
            USE_QWEN_EMBEDDINGS: Use local Qwen model for embeddings (default: false)
            USE_COPILOT_EMBEDDINGS: Use GitHub Copilot for embeddings (default: true)
            USE_CONTEXTUAL_EMBEDDINGS: Use contextual embeddings for better retrieval (default: true)
            
            # Rate limiting (from .env)
            COPILOT_REQUESTS_PER_MINUTE: Rate limit for Copilot API (default: 60)
            
        Returns:
            ChunkerConfig instance with values from environment or defaults
        """
        return cls(
            max_chunk_size=int(os.getenv("MANUAL_MAX_CHUNK_SIZE", "1000")),
            min_chunk_size=int(os.getenv("MANUAL_MIN_CHUNK_SIZE", "100")),
            chunk_overlap=int(os.getenv("MANUAL_CHUNK_OVERLAP", "50")),
            size_metric=os.getenv("MANUAL_SIZE_METRIC", "characters"),
            embedding_model=os.getenv("MANUAL_EMBEDDING_MODEL", "text-embedding-3-small"),
            summary_model=os.getenv("MANUAL_SUMMARY_MODEL", "iflow/qwen3-coder-plus"),
            use_qwen_embeddings=os.getenv("USE_QWEN_EMBEDDINGS", "false").lower() == "true",
            use_copilot_embeddings=os.getenv("USE_COPILOT_EMBEDDINGS", "true").lower() == "true",
            generate_summaries=os.getenv("MANUAL_GENERATE_SUMMARIES", "true").lower() == "true",
            generate_embeddings=os.getenv("MANUAL_GENERATE_EMBEDDINGS", "true").lower() == "true",
            use_contextual_embeddings=os.getenv("USE_CONTEXTUAL_EMBEDDINGS", "true").lower() == "true",
            copilot_requests_per_minute=int(os.getenv("COPILOT_REQUESTS_PER_MINUTE", "60")),
        )
    
    def validate(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if self.max_chunk_size <= 0:
            raise ValueError(f"max_chunk_size must be positive, got {self.max_chunk_size}")
        
        if self.min_chunk_size <= 0:
            raise ValueError(f"min_chunk_size must be positive, got {self.min_chunk_size}")
        
        if self.min_chunk_size > self.max_chunk_size:
            raise ValueError(
                f"min_chunk_size ({self.min_chunk_size}) cannot be greater than "
                f"max_chunk_size ({self.max_chunk_size})"
            )
        
        if self.chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {self.chunk_overlap}")
        
        if self.chunk_overlap >= self.max_chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"max_chunk_size ({self.max_chunk_size})"
            )
        
        if self.size_metric not in ("characters", "tokens"):
            raise ValueError(f"size_metric must be 'characters' or 'tokens', got {self.size_metric}")
        
        if self.embedding_batch_size <= 0:
            raise ValueError(f"embedding_batch_size must be positive, got {self.embedding_batch_size}")
        
        if self.max_summary_length <= 0:
            raise ValueError(f"max_summary_length must be positive, got {self.max_summary_length}")
        
        if self.summary_timeout_seconds <= 0:
            raise ValueError(f"summary_timeout_seconds must be positive, got {self.summary_timeout_seconds}")
        
        if self.embedding_retry_attempts < 0:
            raise ValueError(f"embedding_retry_attempts must be non-negative, got {self.embedding_retry_attempts}")
        
        if self.embedding_retry_backoff <= 0:
            raise ValueError(f"embedding_retry_backoff must be positive, got {self.embedding_retry_backoff}")
