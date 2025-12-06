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