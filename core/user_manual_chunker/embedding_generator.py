"""
Embedding generator for user manual chunks.

Generates vector embeddings for document chunks using the flexible
embedding infrastructure from utils.py, which supports:
- Qwen embeddings (local model)
- GitHub Copilot embeddings
- OpenAI embeddings (fallback)

The embedding provider is selected based on environment variables:
- USE_QWEN_EMBEDDINGS=true: Use local Qwen model
- USE_COPILOT_EMBEDDINGS=true: Use GitHub Copilot
- Otherwise: Use OpenAI (default)
"""

import numpy as np
from typing import List, Optional
import sys
import os
import logging
import time
from collections import deque

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the flexible embedding functions from utils
from server.utils import create_embeddings_batch, create_embedding
from .interfaces import DocumentChunk
from .data_models import ProcessedChunk

# Set up logging
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Implements a simple token bucket algorithm to limit the rate of API requests.
    """
    
    def __init__(self, max_requests: int = 60, time_window: float = 60.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def acquire(self) -> None:
        """
        Acquire permission to make a request, blocking if necessary.
        """
        now = time.time()
        
        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Check if we're at the limit
        if len(self.requests) >= self.max_requests:
            # Calculate how long to wait
            oldest_request = self.requests[0]
            wait_time = (oldest_request + self.time_window) - now
            
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                # Recursively try again
                return self.acquire()
        
        # Record this request
        self.requests.append(now)


class EmbeddingGenerator:
    """
    Generates embeddings for document chunks.
    
    Integrates with existing embedding infrastructure (Copilot API),
    implements batch processing for efficiency, preserves code syntax,
    normalizes vectors for cosine similarity, and includes retry logic
    with exponential backoff and rate limiting.
    """
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 32,
        normalize: bool = True,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        rate_limit_requests: int = 60,
        rate_limit_window: float = 60.0
    ):
        """
        Initialize the embedding generator.
        
        Args:
            model: Embedding model to use (default: text-embedding-3-small)
            batch_size: Number of chunks to process in each batch
            normalize: Whether to normalize vectors for cosine similarity
            max_retries: Maximum number of retry attempts for failed requests
            initial_retry_delay: Initial delay in seconds for exponential backoff
            rate_limit_requests: Maximum requests per time window
            rate_limit_window: Time window in seconds for rate limiting
        """
        self.model = model
        self.batch_size = batch_size
        self.normalize = normalize
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
    
    def generate_embeddings(
        self,
        chunks: List[DocumentChunk],
        summaries: Optional[List[Optional[str]]] = None
    ) -> List[np.ndarray]:
        """
        Generate embeddings for a list of chunks in batches.
        
        Combines chunk content with summaries for better retrieval.
        This improves search quality by including semantic context from summaries.
        
        Implements retry with exponential backoff and rate limiting.
        Handles batch failures by processing chunks individually.
        
        Args:
            chunks: List of DocumentChunk objects to embed
            summaries: Optional list of summaries (one per chunk).
                      If provided, summaries are appended to chunk content
                      before embedding for better semantic representation.
            
        Returns:
            List of embedding vectors as numpy arrays
            
        Example:
            Without summary: "The DML language supports..."
            With summary: "Summary: Overview of DML language features\n\nThe DML language supports..."
        """
        if not chunks:
            return []
        
        # Extract text content from chunks, optionally combining with summaries
        texts = []
        for i, chunk in enumerate(chunks):
            base_text = self._prepare_text_for_embedding(chunk)
            
            # Combine with summary if available (improves retrieval quality)
            if summaries and i < len(summaries) and summaries[i]:
                combined_text = f"Summary: {summaries[i]}\n\n{base_text}"
                texts.append(combined_text)
            else:
                texts.append(base_text)
        
        # Generate embeddings in batches
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            # Try batch processing with retry
            batch_embeddings = self._generate_batch_with_retry(batch_texts, batch_num)
            
            if batch_embeddings is None:
                # Batch failed after retries, try individual chunks
                logger.warning(f"Batch {batch_num} failed, processing chunks individually")
                batch_embeddings = []
                
                for j, text in enumerate(batch_texts):
                    embedding = self._generate_single_with_retry(text, f"batch {batch_num}, chunk {j}")
                    batch_embeddings.append(embedding)
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def _generate_batch_with_retry(
        self,
        texts: List[str],
        batch_num: int
    ) -> Optional[List[np.ndarray]]:
        """
        Generate embeddings for a batch with retry logic.
        
        Uses the flexible embedding system from utils.py that supports:
        - Qwen embeddings (local model)
        - GitHub Copilot embeddings
        - OpenAI embeddings (fallback)
        
        Args:
            texts: List of text strings to embed
            batch_num: Batch number for logging
            
        Returns:
            List of embedding vectors, or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.acquire()
                
                # Use flexible embedding system from utils.py
                # This automatically handles Qwen -> Copilot -> OpenAI fallback
                batch_embeddings = create_embeddings_batch(texts)
                
                # Convert to numpy arrays
                batch_embeddings_np = [np.array(emb, dtype=np.float32) for emb in batch_embeddings]
                
                # Normalize if requested
                if self.normalize:
                    batch_embeddings_np = self._normalize_vectors(batch_embeddings_np)
                
                logger.info(f"Successfully generated embeddings for batch {batch_num}")
                return batch_embeddings_np
                
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for batch {batch_num}: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.initial_retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for batch {batch_num}")
                    return None
        
        return None
    
    def generate_embedding_single(
        self,
        chunk: DocumentChunk
    ) -> np.ndarray:
        """
        Generate embedding for a single chunk with retry logic.
        
        Args:
            chunk: DocumentChunk to embed
            
        Returns:
            Embedding vector as numpy array (returns zero vector on failure)
        """
        text = self._prepare_text_for_embedding(chunk)
        return self._generate_single_with_retry(text, "single chunk")
    
    def _generate_single_with_retry(
        self,
        text: str,
        identifier: str
    ) -> np.ndarray:
        """
        Generate embedding for a single text with retry logic.
        
        Uses the flexible embedding system from utils.py that supports:
        - Qwen embeddings (local model)
        - GitHub Copilot embeddings
        - OpenAI embeddings (fallback)
        
        Args:
            text: Text to embed
            identifier: Identifier for logging
            
        Returns:
            Embedding vector as numpy array (returns zero vector on failure)
        """
        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.acquire()
                
                # Use flexible embedding system from utils.py
                # This automatically handles Qwen -> Copilot -> OpenAI fallback
                embedding = create_embedding(text)
                
                # Convert to numpy array
                embedding_np = np.array(embedding, dtype=np.float32)
                
                # Normalize if requested
                if self.normalize:
                    embedding_np = self._normalize_vector(embedding_np)
                
                return embedding_np
                
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {identifier}: {e}"
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.initial_retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"All retry attempts exhausted for {identifier}")
        
        # Return zero embedding as fallback (Requirement 3.5)
        logger.warning(f"Using zero embedding for {identifier}")
        embedding_dim = 1536  # text-embedding-3-small dimension
        return np.zeros(embedding_dim, dtype=np.float32)
    
    def _prepare_text_for_embedding(self, chunk: DocumentChunk) -> str:
        """
        Prepare chunk text for embedding, preserving code syntax.
        
        Code blocks are preserved with their language markers to maintain
        syntax information in the embedding.
        
        Args:
            chunk: DocumentChunk to prepare
            
        Returns:
            Text string ready for embedding
        """
        # The chunk content already includes code blocks with proper formatting
        # from the Section.get_text_content() method, which preserves code syntax
        # with triple backticks and language identifiers
        return chunk.content
    
    def _normalize_vectors(
        self,
        embeddings: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Normalize embedding vectors for cosine similarity.
        
        Each vector is normalized to unit length (L2 norm = 1.0).
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            List of normalized embedding vectors
        """
        normalized = []
        for emb in embeddings:
            normalized.append(self._normalize_vector(emb))
        return normalized
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """
        Normalize a single vector to unit length.
        
        Args:
            vector: Embedding vector to normalize
            
        Returns:
            Normalized vector with L2 norm = 1.0
        """
        norm = np.linalg.norm(vector)
        if norm == 0:
            # Return zero vector if input is zero
            return vector
        return vector / norm
    
    def add_embeddings_to_chunks(
        self,
        chunks: List[DocumentChunk],
        processed_chunks: List[ProcessedChunk]
    ) -> None:
        """
        Generate embeddings and add them to ProcessedChunk objects.
        
        Combines chunk content with summaries for better retrieval.
        This is a convenience method that generates embeddings for chunks
        and updates the corresponding ProcessedChunk objects in-place.
        
        Args:
            chunks: List of DocumentChunk objects
            processed_chunks: List of ProcessedChunk objects to update
            
        Raises:
            ValueError: If chunks and processed_chunks have different lengths
            RuntimeError: If embedding generation fails
        """
        if len(chunks) != len(processed_chunks):
            raise ValueError(
                f"Mismatch between chunks ({len(chunks)}) and "
                f"processed_chunks ({len(processed_chunks)})"
            )
        
        # Extract summaries from processed chunks
        summaries = [pc.summary for pc in processed_chunks]
        
        # Generate all embeddings (combining content + summary)
        embeddings = self.generate_embeddings(chunks, summaries)
        
        # Add embeddings to processed chunks
        for processed_chunk, embedding in zip(processed_chunks, embeddings):
            processed_chunk.embedding = embedding
