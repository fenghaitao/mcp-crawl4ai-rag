"""
Abstract base classes for database backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import contextmanager
import os


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics and information."""
        pass
    
    @abstractmethod
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            with backend.transaction():
                backend.store_file_version(...)
                backend.store_chunks(...)
                # If any operation fails, transaction is rolled back
        
        Note: ChromaDB doesn't support transactions, so this is best-effort.
        Supabase/PostgreSQL supports full ACID transactions.
        """
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections/tables in the database."""
        pass
    
    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Delete a specific collection/table."""
        pass
    
    @abstractmethod
    def delete_all_data(self) -> bool:
        """Delete all data from the database."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if database connection is active."""
        pass
    
    @abstractmethod
    def get_backend_name(self) -> str:
        """Get the backend name."""
        pass
    
    @abstractmethod
    def get_config_info(self) -> Dict[str, str]:
        """Get configuration information for display."""
        pass
    
    @abstractmethod
    def apply_schema(self, schema_files: List[str]) -> bool:
        """Apply schema files to the database."""
        pass
    
    @abstractmethod
    def drop_schema(self, table_names: List[str]) -> bool:
        """Drop tables/collections from the database."""
        pass
    
    @abstractmethod
    def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """Get dynamic schema information from the database."""
        pass
    
    # Document Ingest Interface Methods
    @abstractmethod
    def check_file_exists(self, file_path: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if file already exists in database with same hash.
        
        Returns:
            Dict with file info if exists, None otherwise
        """
        pass
    
    @abstractmethod
    def remove_file_data(self, file_path: str) -> bool:
        """
        Remove existing file and its chunks from database.
        Removes ALL versions of the file.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def remove_file_version(self, file_path: str, commit_sha: str) -> bool:
        """
        Remove a specific version of a file by commit SHA.
        
        Args:
            file_path: Path to the file
            commit_sha: Full or partial commit SHA (will match prefix)
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def store_file_record(self, file_path: str, content_hash: str, file_size: int, content_type: str = 'documentation') -> str:
        """
        Store file record in database.
        
        Returns:
            File ID
        """
        pass
    
    @abstractmethod
    def store_chunks(self, file_id: str, chunks: List[Any], file_path: str) -> Dict[str, int]:
        """
        Store content chunks in database.
        
        Args:
            file_id: File identifier
            chunks: List of processed chunks
            file_path: Original file path
            
        Returns:
            Dict with statistics (chunks count, words count)
        """
        pass
    
    @abstractmethod
    def update_file_statistics(self, file_id: str, chunk_count: int, word_count: int) -> bool:
        """
        Update file record with processing statistics.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # Repository operations
    @abstractmethod
    def store_repository(self, repo_url: str, repo_name: str) -> int:
        """
        Store repository record and return repo_id.
        
        Args:
            repo_url: Git remote URL
            repo_name: Repository name for display
            
        Returns:
            Repository ID
        """
        pass
    
    @abstractmethod
    def get_repository(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """
        Get repository by URL.
        
        Args:
            repo_url: Git remote URL
            
        Returns:
            Repository dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_repository_by_id(self, repo_id: int) -> Optional[Dict[str, Any]]:
        """
        Get repository by ID.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Repository dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_repository_last_ingested(self, repo_id: int) -> bool:
        """
        Update last_ingested_at timestamp for repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # File operations with temporal support
    @abstractmethod
    def store_file_version(self, file_version: Dict[str, Any]) -> int:
        """
        Store new file version and update previous version's valid_until.
        
        Args:
            file_version: Dict containing file version data
            
        Returns:
            File version ID
        """
        pass
    
    @abstractmethod
    def get_current_file(self, repo_id: int, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get currently valid version of a file (valid_until IS NULL).
        
        Args:
            repo_id: Repository ID
            file_path: Relative file path
            
        Returns:
            File version dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_file_at_time(self, repo_id: int, file_path: str, timestamp: Any) -> Optional[Dict[str, Any]]:
        """
        Get file version valid at specific timestamp.
        
        Args:
            repo_id: Repository ID
            file_path: Relative file path
            timestamp: Point in time (datetime)
            
        Returns:
            File version dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_file_at_commit(self, repo_id: int, file_path: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """
        Get file version from specific commit.
        
        Args:
            repo_id: Repository ID
            file_path: Relative file path
            commit_sha: Git commit SHA
            
        Returns:
            File version dict if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_file_history(self, repo_id: int, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all versions of a file ordered by valid_from.
        
        Args:
            repo_id: Repository ID
            file_path: Relative file path
            limit: Maximum number of versions to return
            
        Returns:
            List of file version dicts
        """
        pass
    
    @abstractmethod
    def list_files(self, repo_id: Optional[int] = None, content_type: Optional[str] = None,
                   current_only: bool = True, limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """
        List files with filtering and pagination.
        
        Args:
            repo_id: Filter by repository ID (optional)
            content_type: Filter by content type (optional)
            current_only: Only return current versions (valid_until IS NULL)
            limit: Maximum number of files to return
            offset: Number of files to skip
            
        Returns:
            Tuple of (file_list, total_count)
        """
        pass
    
    @abstractmethod
    def semantic_search(self, query_text: str, limit: int = 5, 
                       content_type: Optional[str] = None,
                       threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search on content chunks using embeddings.
        
        Args:
            query_text: The search query text
            limit: Maximum number of results to return
            content_type: Filter by content type (optional)
            threshold: Minimum similarity threshold (optional)
            
        Returns:
            List of matching chunks with similarity scores
        """
        pass
    
    @abstractmethod
    def get_chunks_by_file_id(self, file_id: int) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific file ID ordered by chunk_number.
        
        Args:
            file_id: File version ID
            
        Returns:
            List of chunk dictionaries ordered by chunk_number
        """
        pass
    
    @abstractmethod
    def cleanup_orphaned_chunks(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Find and optionally remove orphaned chunks that have no corresponding file records.
        
        Args:
            dry_run: If True, only analyze without removing chunks
            
        Returns:
            Dict with statistics about orphaned chunks:
                - total_chunks: Total number of chunks in database
                - valid_files: Number of valid file records
                - orphaned_chunks: Number of orphaned chunks found
                - orphan_groups: Dict grouping orphans by file_id
                - removed: Number of chunks removed (0 if dry_run)
        """
        pass