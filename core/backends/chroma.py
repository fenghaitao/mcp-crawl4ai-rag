"""
ChromaDB backend implementation.
"""

import os
from pathlib import Path
from typing import Dict, Any, List

from .base import DatabaseBackend


class ChromaBackend(DatabaseBackend):
    """ChromaDB backend implementation."""
    
    def __init__(self):
        self._client = None
        self._chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._chroma_path)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize ChromaDB client: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        stats = {
            'backend': 'chroma',
            'path': self._chroma_path,
            'path_exists': Path(self._chroma_path).exists(),
            'connected': self.is_connected(),
            'collections': {}
        }
        
        if self.is_connected():
            try:
                collections = self._client.list_collections()
                for collection in collections:
                    try:
                        count = collection.count()
                        stats['collections'][collection.name] = count
                    except Exception:
                        stats['collections'][collection.name] = 'Error'
            except Exception:
                stats['collections'] = 'Error fetching collections'
        
        return stats
    
    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB."""
        if not self.is_connected():
            return []
        
        try:
            collections = self._client.list_collections()
            return [c.name for c in collections]
        except Exception:
            return []
    
    def delete_collection(self, name: str) -> bool:
        """Delete a specific collection."""
        try:
            self._client.delete_collection(name)
            return True
        except Exception:
            return False
    
    def delete_all_data(self) -> bool:
        """Delete all collections."""
        success = True
        collections = self.list_collections()
        for collection_name in collections:
            if not self.delete_collection(collection_name):
                success = False
        return success
    
    def is_connected(self) -> bool:
        """Check if ChromaDB connection is active."""
        try:
            self._client.list_collections()
            return True
        except Exception:
            return False
    
    def get_backend_name(self) -> str:
        """Get backend name."""
        return "chroma"
    
    def get_config_info(self) -> Dict[str, str]:
        """Get ChromaDB configuration information."""
        return {
            'Path': self._chroma_path,
            'Path Exists': '✅ Yes' if Path(self._chroma_path).exists() else '❌ No',
            'Connection': '✅ Active' if self.is_connected() else '❌ Failed'
        }