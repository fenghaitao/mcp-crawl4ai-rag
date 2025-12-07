"""
Query Service - Query interface for ingested documents.

This service provides methods for querying files and chunks with:
- Temporal queries (current, at specific time, at specific commit)
- File listing with filtering and pagination
- File history tracking
- Chunk retrieval and search
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class QueryService:
    """Service for querying ingested documents."""
    
    def __init__(self, backend):
        """
        Initialize query service.
        
        Args:
            backend: DatabaseBackend instance
            
        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
        """
        self.backend = backend
    
    def query_file(self, repo_url: str, file_path: str,
                  commit_sha: Optional[str] = None,
                  timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Query file with temporal constraints.
        
        Args:
            repo_url: Repository URL
            file_path: Relative file path
            commit_sha: Specific commit (optional)
            timestamp: Point in time (optional)
            
        Returns:
            FileVersion dict or None
            
        Requirements: 7.1, 7.2, 7.3
        """
        # Get repository by URL
        repo = self.backend.get_repository(repo_url)
        if not repo:
            return None
        
        repo_id = repo['id'] if isinstance(repo, dict) else repo.id
        
        # Call appropriate backend method based on parameters
        if commit_sha:
            # Query by commit SHA (Requirement 7.3)
            return self.backend.get_file_at_commit(repo_id, file_path, commit_sha)
        elif timestamp:
            # Query at specific timestamp (Requirement 7.2)
            return self.backend.get_file_at_time(repo_id, file_path, timestamp)
        else:
            # Query current version (Requirement 7.1)
            return self.backend.get_current_file(repo_id, file_path)
    
    def list_files(self, repo_url: Optional[str] = None,
                  content_type: Optional[str] = None,
                  current_only: bool = True,
                  limit: int = 100, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        List files with filtering.
        
        Args:
            repo_url: Repository URL (optional filter)
            content_type: Content type filter (optional)
            current_only: Only return current versions
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Tuple of (files list, total_count)
            
        Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
        """
        # Get repository ID if URL specified (Requirement 8.3)
        repo_id = None
        if repo_url:
            repo = self.backend.get_repository(repo_url)
            if repo:
                repo_id = repo['id'] if isinstance(repo, dict) else repo.id
            else:
                # Repository not found, return empty results
                return ([], 0)
        
        # Call backend list_files with filters (Requirements 8.1, 8.2, 8.4, 8.5)
        return self.backend.list_files(
            repo_id=repo_id,
            content_type=content_type,
            current_only=current_only,
            limit=limit,
            offset=offset
        )
    
    def get_file_history(self, repo_url: str, file_path: str,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get version history for a file.
        
        Args:
            repo_url: Repository URL
            file_path: Relative file path
            limit: Maximum number of versions to return
            
        Returns:
            List of FileVersion dicts ordered by valid_from DESC
            
        Requirements: 7.1.1, 7.1.2, 7.1.3, 7.1.4, 7.1.5
        """
        # Get repository by URL
        repo = self.backend.get_repository(repo_url)
        if not repo:
            return []
        
        repo_id = repo['id'] if isinstance(repo, dict) else repo.id
        
        # Call backend get_file_history
        return self.backend.get_file_history(repo_id, file_path, limit)
    
    def get_file_chunks(self, file_version_id: int) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific file version.
        
        Args:
            file_version_id: File version ID
            
        Returns:
            List of chunk dictionaries ordered by chunk_number
            
        Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
        """
        # Query content_chunks by file_id, ordered by chunk_number
        return self.backend.get_chunks_by_file_id(file_version_id)
    
    def search_chunks(self, content_type: Optional[str] = None,
                     has_code: Optional[bool] = None,
                     metadata_filter: Optional[Dict[str, Any]] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search chunks by metadata.
        
        Args:
            content_type: Content type filter (optional)
            has_code: Filter for chunks with code blocks (optional)
            metadata_filter: Additional metadata filters (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching chunk dictionaries
            
        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
        """
        # Build query with filters and apply AND logic (Requirement 10.3)
        return self.backend.search_chunks(
            content_type=content_type,
            has_code=has_code,
            metadata_filter=metadata_filter,
            limit=limit
        )
