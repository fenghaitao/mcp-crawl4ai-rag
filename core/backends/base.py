"""
Abstract base classes for database backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import os


class DatabaseBackend(ABC):
    """Abstract base class for database backends."""
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics and information."""
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