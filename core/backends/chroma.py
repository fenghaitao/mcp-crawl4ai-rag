"""
ChromaDB backend implementation.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

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
    
    # Document Ingest Interface Implementation
    def check_file_exists(self, file_path: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file already exists in database with same hash."""
        try:
            files_collection = self._client.get_collection('files')
            results = files_collection.get(
                where={"$and": [{"file_path": file_path}, {"content_hash": content_hash}]}
            )
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'file_path': results['metadatas'][0]['file_path'],
                    'content_hash': results['metadatas'][0]['content_hash'],
                    'chunk_count': results['metadatas'][0].get('chunk_count', 0),
                    'word_count': results['metadatas'][0].get('word_count', 0)
                }
            return None
        except Exception:
            return None
    
    def remove_file_data(self, file_path: str) -> bool:
        """Remove existing file and its chunks from database."""
        try:
            # Get file record first
            files_collection = self._client.get_collection('files')
            file_results = files_collection.get(
                where={"file_path": file_path}
            )
            
            if file_results['ids']:
                file_id = file_results['ids'][0]
                
                # Remove chunks first
                try:
                    chunks_collection = self._client.get_collection('content_chunks')
                    chunk_results = chunks_collection.get(
                        where={"file_id": file_id}
                    )
                    if chunk_results['ids']:
                        chunks_collection.delete(ids=chunk_results['ids'])
                except Exception:
                    pass  # Collection might not exist or have no chunks
                
                # Remove file record
                files_collection.delete(ids=[file_id])
            
            return True
        except Exception:
            return False
    
    def store_file_record(self, file_path: str, content_hash: str, file_size: int, content_type: str = 'documentation') -> str:
        """Store file record and return file ID."""
        import hashlib
        
        files_collection = self._client.get_or_create_collection('files')
        
        # Generate unique file ID
        file_id = f"file_{hashlib.md5(file_path.encode()).hexdigest()[:16]}"
        
        file_metadata = {
            'file_path': file_path,
            'content_hash': content_hash,
            'file_size': file_size,
            'content_type': content_type,
            'word_count': 0,
            'chunk_count': 0
        }
        
        files_collection.add(
            ids=[file_id],
            documents=[file_path],  # Use file path as document content
            metadatas=[file_metadata]
        )
        return file_id
    
    def store_chunks(self, file_id: str, chunks: List[Any], file_path: str) -> Dict[str, int]:
        """Store chunks in database and return statistics."""
        chunks_collection = self._client.get_or_create_collection('content_chunks')
        
        chunk_ids = []
        chunk_documents = []
        chunk_metadatas = []
        chunk_embeddings = []
        total_words = 0
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            chunk_documents.append(chunk.content)
            
            # Prepare metadata
            word_count = chunk.metadata.char_count // 5  # Rough word count estimate
            metadata = {
                'file_id': file_id,
                'url': file_path,
                'chunk_number': i,
                'content_type': 'documentation',
                'summary': chunk.summary if chunk.summary else '',
                'title': chunk.metadata.heading_hierarchy[-1] if chunk.metadata.heading_hierarchy else '',
                'section': ' > '.join(chunk.metadata.heading_hierarchy),
                'word_count': word_count,
                'has_code': chunk.metadata.contains_code,
                'heading_hierarchy': chunk.metadata.heading_hierarchy,
                'language_hints': chunk.metadata.code_languages
            }
            chunk_metadatas.append(metadata)
            
            # Add embedding if available
            if chunk.embedding is not None:
                # Convert numpy array to list if needed
                embedding = chunk.embedding
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                chunk_embeddings.append(embedding)
            
            total_words += word_count
        
        total_chunks = len(chunks)
        
        # Add chunks to collection
        if chunk_ids:
            if chunk_embeddings and len(chunk_embeddings) == len(chunk_ids):
                chunks_collection.add(
                    ids=chunk_ids,
                    documents=chunk_documents,
                    metadatas=chunk_metadatas,
                    embeddings=chunk_embeddings
                )
            else:
                chunks_collection.add(
                    ids=chunk_ids,
                    documents=chunk_documents,
                    metadatas=chunk_metadatas
                )
        
        return {'chunks': total_chunks, 'words': total_words}
    
    def update_file_statistics(self, file_id: str, chunk_count: int, word_count: int) -> bool:
        """Update file record with processing statistics."""
        try:
            files_collection = self._client.get_collection('files')
            
            # Get current file metadata
            current_file = files_collection.get(ids=[file_id])
            if not current_file['ids']:
                return False
            
            # Update metadata
            current_metadata = current_file['metadatas'][0]
            current_metadata['word_count'] = word_count
            current_metadata['chunk_count'] = chunk_count
            
            files_collection.update(
                ids=[file_id],
                metadatas=[current_metadata]
            )
            return True
        except Exception:
            return False