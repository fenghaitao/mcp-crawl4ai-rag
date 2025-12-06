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
    
    def apply_schema(self, schema_files: List[str]) -> bool:
        """Apply schema files to ChromaDB (creates collections based on schema)."""
        if not self.is_connected():
            raise ConnectionError("Not connected to ChromaDB")
        
        # For ChromaDB, we don't apply SQL schemas directly
        # Instead, we ensure the basic collections exist
        try:
            # Create default collections if they don't exist
            collection_names = ['files', 'content_chunks']
            
            for collection_name in collection_names:
                try:
                    # Try to get the collection first
                    collection = self._client.get_collection(collection_name)
                    print(f"✅ Collection '{collection_name}' already exists")
                except Exception:
                    # Collection doesn't exist, create it
                    try:
                        collection = self._client.create_collection(
                            name=collection_name,
                            metadata={"hnsw:space": "cosine"}
                        )
                        print(f"✅ Created collection '{collection_name}'")
                    except Exception as create_error:
                        print(f"❌ Error creating collection '{collection_name}': {create_error}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error setting up ChromaDB collections: {e}")
            return False
    
    def drop_schema(self, table_names: List[str]) -> bool:
        """Drop collections from ChromaDB."""
        if not self.is_connected():
            raise ConnectionError("Not connected to ChromaDB")
        
        success = True
        for collection_name in table_names:
            try:
                self._client.delete_collection(collection_name)
            except Exception as e:
                print(f"Error dropping collection {collection_name}: {e}")
                success = False
        
        return success
    
    def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """Get dynamic schema information from ChromaDB."""
        if not self.is_connected():
            return {}
        
        schema_info = {}
        
        try:
            # List all collections and get their info
            collections = self._client.list_collections()
            
            for collection in collections:
                try:
                    # Get collection info
                    col_obj = self._client.get_collection(collection.name)
                    count = col_obj.count()
                    
                    schema_info[collection.name] = {
                        'description': self._get_collection_description(collection.name),
                        'record_count': count,
                        'type': 'collection'
                    }
                    
                except Exception as e:
                    schema_info[collection.name] = {
                        'description': self._get_collection_description(collection.name),
                        'record_count': 'Error',
                        'type': 'collection'
                    }
                    
        except Exception as e:
            print(f"Error getting ChromaDB schema info: {e}")
        
        return schema_info
    
    def _get_collection_description(self, collection_name: str) -> str:
        """Get description for ChromaDB collections."""
        descriptions = {
            'sources': 'Source metadata and summaries',
            'crawled_pages': 'Chunked documentation with embeddings',
            'code_examples': 'Code snippets with summaries',
            'files': 'Individual files with content hashing and metadata',
            'content_chunks': 'File-based text chunks with embeddings'
        }
        return descriptions.get(collection_name, f'Collection: {collection_name}')
    
    def list_all_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List data from a specific collection."""
        if not self.is_connected():
            return []
        
        try:
            collection = self._client.get_collection(table_name)
            result = collection.get(limit=limit)
            
            # Convert ChromaDB format to list of dictionaries
            data = []
            for i, doc_id in enumerate(result['ids']):
                item = {
                    'id': doc_id,
                    'document': result['documents'][i] if i < len(result['documents']) else '',
                    'metadata': result['metadatas'][i] if i < len(result['metadatas']) else {}
                }
                data.append(item)
            
            return data
            
        except Exception as e:
            print(f"Error querying {table_name}: {e}")
            return []