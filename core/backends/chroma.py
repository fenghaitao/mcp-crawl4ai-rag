"""
ChromaDB backend implementation.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import DatabaseBackend
from contextlib import contextmanager


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
    
    def _get_or_create_metadata_collection(self, name: str):
        """
        Get or create a collection for metadata (files, repositories).
        These collections store metadata only and use documents for searchability.
        No embeddings are needed - ChromaDB will use default embedding function.
        """
        try:
            # Use get_or_create without specifying embedding function
            # ChromaDB will use its default embedding function
            return self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "l2"}
            )
        except Exception as e:
            raise e
    
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
    
    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.
        
        Note: ChromaDB doesn't support true transactions.
        This is a no-op for API compatibility with Supabase backend.
        Operations are executed immediately and cannot be rolled back.
        """
        try:
            yield self
        except Exception as e:
            # ChromaDB doesn't support rollback
            # Log the error and re-raise
            import logging
            logging.getLogger(__name__).error(f"Operation failed (no rollback available): {e}")
            raise
    
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
            collection_names = ['repositories', 'files', 'content_chunks']
            
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
            'repositories': 'Git repositories containing documentation and source code',
            'files': 'File versions with temporal validity tracking',
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
        """Remove existing file and its chunks from database.
        
        Removes ALL versions of the file matching the given path.
        """
        try:
            # Get all file records matching this path
            files_collection = self._client.get_collection('files')
            file_results = files_collection.get(
                where={"file_path": file_path}
            )
            
            if file_results['ids']:
                # Remove chunks for all file versions
                try:
                    chunks_collection = self._client.get_collection('content_chunks')
                    for file_id in file_results['ids']:
                        # Convert file_id to int for chunk query (chunks store file_id as int)
                        file_id_int = int(file_id) if isinstance(file_id, str) and file_id.isdigit() else file_id
                        chunk_results = chunks_collection.get(
                            where={"file_id": file_id_int}
                        )
                        if chunk_results['ids']:
                            chunks_collection.delete(ids=chunk_results['ids'])
                except Exception as e:
                    # Log but don't fail - collection might not exist or have no chunks
                    import logging
                    logging.getLogger(__name__).warning(f"Error removing chunks: {e}")
                
                # Remove all file records
                files_collection.delete(ids=file_results['ids'])
            
            return True
        except Exception:
            return False
    
    def remove_file_version(self, file_path: str, commit_sha: str) -> bool:
        """Remove a specific version of a file by commit SHA.
        
        Args:
            file_path: Path to the file
            commit_sha: Full or partial commit SHA (will match prefix)
        """
        try:
            # Get all file records matching this path
            files_collection = self._client.get_collection('files')
            file_results = files_collection.get(
                where={"file_path": file_path}
            )
            
            if not file_results['ids']:
                return False
            
            # Find matching commit(s)
            matching_ids = []
            for i, file_id in enumerate(file_results['ids']):
                file_commit = file_results['metadatas'][i].get('commit_sha', '')
                if file_commit.startswith(commit_sha):
                    matching_ids.append(file_id)
            
            if not matching_ids:
                return False
            
            # Remove chunks for matching versions
            try:
                chunks_collection = self._client.get_collection('content_chunks')
                for file_id in matching_ids:
                    # Convert file_id to int for chunk query (chunks store file_id as int)
                    file_id_int = int(file_id) if isinstance(file_id, str) and file_id.isdigit() else file_id
                    chunk_results = chunks_collection.get(
                        where={"file_id": file_id_int}
                    )
                    if chunk_results['ids']:
                        chunks_collection.delete(ids=chunk_results['ids'])
            except Exception as e:
                # Log but don't fail - collection might not exist or have no chunks
                import logging
                logging.getLogger(__name__).warning(f"Error removing chunks: {e}")
            
            # Remove matching file records
            files_collection.delete(ids=matching_ids)
            
            return True
        except Exception:
            return False
    
    def store_file_record(self, file_path: str, content_hash: str, file_size: int, content_type: str = 'documentation') -> str:
        """Store file record and return file ID."""
        import hashlib
        
        files_collection = self._get_or_create_metadata_collection('files')
        
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
                'heading_hierarchy': ' > '.join(chunk.metadata.heading_hierarchy),  # Convert list to string
                'language_hints': ', '.join(chunk.metadata.code_languages) if chunk.metadata.code_languages else ''  # Convert list to string
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
            
            # Ensure file_id is a string (it might be an int from store_file_version)
            file_id_str = str(file_id)
            
            # Get current file metadata
            current_file = files_collection.get(ids=[file_id_str])
            if not current_file['ids']:
                return False
            
            # Update metadata
            current_metadata = current_file['metadatas'][0]
            current_metadata['word_count'] = word_count
            current_metadata['chunk_count'] = chunk_count
            
            files_collection.update(
                ids=[file_id_str],
                metadatas=[current_metadata]
            )
            return True
        except Exception:
            return False

    # Repository operations implementation
    def store_repository(self, repo_url: str, repo_name: str) -> int:
        """Store repository record and return repo_id."""
        import hashlib
        from datetime import datetime
        
        try:
            repos_collection = self._get_or_create_metadata_collection('repositories')
            
            # Generate unique repo ID
            repo_id = int(hashlib.md5(repo_url.encode()).hexdigest()[:8], 16)
            
            # Check if repository already exists
            try:
                existing = repos_collection.get(ids=[str(repo_id)])
                if existing['ids']:
                    # Update last_ingested_at
                    metadata = existing['metadatas'][0]
                    metadata['last_ingested_at'] = datetime.now().isoformat()
                    repos_collection.update(
                        ids=[str(repo_id)],
                        metadatas=[metadata]
                    )
                    return repo_id
            except Exception:
                pass
            
            # Create new repository record
            repo_metadata = {
                'repo_url': repo_url,
                'repo_name': repo_name,
                'created_at': datetime.now().isoformat(),
                'last_ingested_at': datetime.now().isoformat()
            }
            
            repos_collection.add(
                ids=[str(repo_id)],
                documents=[repo_url],
                metadatas=[repo_metadata]
            )
            return repo_id
        except Exception as e:
            raise Exception(f"Failed to store repository: {e}")
    
    def get_repository(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Get repository by URL."""
        import hashlib
        
        try:
            repos_collection = self._client.get_collection('repositories')
            repo_id = int(hashlib.md5(repo_url.encode()).hexdigest()[:8], 16)
            
            result = repos_collection.get(ids=[str(repo_id)])
            if result['ids']:
                metadata = result['metadatas'][0]
                metadata['id'] = repo_id
                return metadata
            return None
        except Exception:
            return None
    
    def get_repository_by_id(self, repo_id: int) -> Optional[Dict[str, Any]]:
        """Get repository by ID."""
        try:
            repos_collection = self._client.get_collection('repositories')
            result = repos_collection.get(ids=[str(repo_id)])
            if result['ids']:
                metadata = result['metadatas'][0]
                metadata['id'] = repo_id
                return metadata
            return None
        except Exception:
            return None
    
    def update_repository_last_ingested(self, repo_id: int) -> bool:
        """Update last_ingested_at timestamp."""
        from datetime import datetime
        
        try:
            repos_collection = self._client.get_collection('repositories')
            result = repos_collection.get(ids=[str(repo_id)])
            if result['ids']:
                metadata = result['metadatas'][0]
                metadata['last_ingested_at'] = datetime.now().isoformat()
                repos_collection.update(
                    ids=[str(repo_id)],
                    metadatas=[metadata]
                )
                return True
            return False
        except Exception:
            return False

    # Temporal file operations implementation
    def store_file_version(self, file_version: Dict[str, Any]) -> int:
        """Store new file version and update previous version's valid_until."""
        import hashlib
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            files_collection = self._get_or_create_metadata_collection('files')
            
            # Generate unique file version ID
            version_key = f"{file_version['repo_id']}_{file_version['commit_sha']}_{file_version['file_path']}"
            file_id = int(hashlib.md5(version_key.encode()).hexdigest()[:8], 16)
            
            # Transaction-like behavior: collect operations first
            updates_to_perform = []
            
            # Find previous current version if exists
            if 'valid_from' in file_version:
                try:
                    current_files = files_collection.get(
                        where={
                            "$and": [
                                {"repo_id": file_version['repo_id']},
                                {"file_path": file_version['file_path']}
                            ]
                        }
                    )
                    
                    # Prepare updates for current versions
                    for i, metadata in enumerate(current_files['metadatas']):
                        # Only update if it's not the same file (different ID)
                        # Current version has valid_until = None or empty string
                        valid_until = metadata.get('valid_until')
                        is_current = valid_until is None or valid_until == ''
                        
                        if is_current and current_files['ids'][i] != str(file_id):
                            updated_metadata = metadata.copy()
                            updated_metadata['valid_until'] = (
                                file_version['valid_from'].isoformat() 
                                if hasattr(file_version['valid_from'], 'isoformat') 
                                else file_version['valid_from']
                            )
                            updates_to_perform.append({
                                'id': current_files['ids'][i],
                                'metadata': updated_metadata
                            })
                except Exception as e:
                    logger.warning(f"Error finding current version for update: {e}")
            
            # Check if this file version already exists
            existing_check = files_collection.get(ids=[str(file_id)])
            
            # Prepare new version metadata
            file_metadata = {}
            
            # If updating existing file, start with existing metadata
            if existing_check['ids']:
                file_metadata = existing_check['metadatas'][0].copy()
            
            # Update with new values from file_version
            for key, value in file_version.items():
                if key == 'valid_until':
                    # Handle valid_until specially
                    if value is None:
                        # Current version - set to empty string (ChromaDB doesn't support removing fields)
                        file_metadata['valid_until'] = ''
                    else:
                        # Historical version - set valid_until
                        if hasattr(value, 'isoformat'):
                            file_metadata['valid_until'] = value.isoformat()
                        else:
                            file_metadata['valid_until'] = value
                elif key == 'valid_from':
                    # Convert datetime to ISO format
                    if hasattr(value, 'isoformat'):
                        file_metadata['valid_from'] = value.isoformat()
                    else:
                        file_metadata['valid_from'] = value
                elif key == 'ingested_at':
                    # Convert datetime to ISO format
                    if hasattr(value, 'isoformat'):
                        file_metadata['ingested_at'] = value.isoformat()
                    else:
                        file_metadata['ingested_at'] = value
                else:
                    # Copy other fields as-is
                    file_metadata[key] = value
            
            # Add file_id to metadata
            file_metadata['id'] = file_id
            
            # Execute operations (best effort transaction)
            try:
                # Perform updates first
                for update in updates_to_perform:
                    files_collection.update(
                        ids=[update['id']],
                        metadatas=[update['metadata']]
                    )
                
                # Add or update file version
                if existing_check['ids']:
                    # Update existing version
                    files_collection.update(
                        ids=[str(file_id)],
                        documents=[file_version['file_path']],
                        metadatas=[file_metadata]
                    )
                else:
                    # Add new version
                    files_collection.add(
                        ids=[str(file_id)],
                        documents=[file_version['file_path']],
                        metadatas=[file_metadata]
                    )
                
                return file_id
                
            except Exception as e:
                logger.error(f"Failed to store file version (partial transaction): {e}")
                # Note: ChromaDB doesn't support rollback, so we log the error
                # Consider implementing a cleanup mechanism in production
                raise Exception(f"Failed to store file version: {e}")
                
        except Exception as e:
            raise Exception(f"Failed to store file version: {e}")
    
    def get_current_file(self, repo_id: int, file_path: str) -> Optional[Dict[str, Any]]:
        """Get currently valid version of a file (valid_until IS NULL)."""
        try:
            files_collection = self._client.get_collection('files')
            results = files_collection.get(
                where={
                    "$and": [
                        {"repo_id": repo_id},
                        {"file_path": file_path}
                    ]
                }
            )
            
            # Find version with valid_until = None or empty string (current version)
            for i, metadata in enumerate(results['metadatas']):
                valid_until = metadata.get('valid_until')
                if valid_until is None or valid_until == '':
                    return metadata
            return None
        except Exception:
            return None
    
    def get_file_at_time(self, repo_id: int, file_path: str, timestamp: Any) -> Optional[Dict[str, Any]]:
        """Get file version valid at specific timestamp."""
        from datetime import datetime
        from ..config.batch_config import config
        
        try:
            files_collection = self._client.get_collection('files')
            
            # Convert timestamp to ISO format for comparison
            if hasattr(timestamp, 'isoformat'):
                timestamp_str = timestamp.isoformat()
            else:
                timestamp_str = str(timestamp)
            
            # Limit results to prevent memory issues
            results = files_collection.get(
                where={
                    "$and": [
                        {"repo_id": repo_id},
                        {"file_path": file_path}
                    ]
                },
                limit=config.temporal_query_limit
            )
            
            # Find version valid at timestamp (optimized)
            best_version = None
            best_valid_from = None
            
            for metadata in results['metadatas']:
                valid_from = metadata.get('valid_from')
                valid_until = metadata.get('valid_until')
                
                if valid_from and valid_from <= timestamp_str:
                    if valid_until is None or valid_until > timestamp_str:
                        # This version is valid at the timestamp
                        if best_valid_from is None or valid_from > best_valid_from:
                            best_version = metadata
                            best_valid_from = valid_from
            
            return best_version
        except Exception:
            return None
    
    def get_file_at_commit(self, repo_id: int, file_path: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Get file version from specific commit."""
        try:
            files_collection = self._client.get_collection('files')
            results = files_collection.get(
                where={
                    "$and": [
                        {"repo_id": repo_id},
                        {"file_path": file_path},
                        {"commit_sha": commit_sha}
                    ]
                }
            )
            
            if results['metadatas']:
                return results['metadatas'][0]
            return None
        except Exception:
            return None
    
    def get_file_history(self, repo_id: int, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all versions of a file ordered by valid_from."""
        try:
            files_collection = self._client.get_collection('files')
            results = files_collection.get(
                where={
                    "$and": [
                        {"repo_id": repo_id},
                        {"file_path": file_path}
                    ]
                }
            )
            
            # Sort by valid_from descending
            versions = sorted(
                results['metadatas'],
                key=lambda x: x.get('valid_from', ''),
                reverse=True
            )
            
            return versions[:limit]
        except Exception:
            return []
    
    def list_files(self, repo_id: Optional[int] = None, content_type: Optional[str] = None,
                   current_only: bool = True, limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """List files with filtering and pagination."""
        try:
            files_collection = self._client.get_collection('files')
            
            # Build where clause
            where_conditions = []
            if repo_id is not None:
                where_conditions.append({"repo_id": repo_id})
            if content_type is not None:
                where_conditions.append({"content_type": content_type})
            
            # Get all matching files
            if where_conditions:
                results = files_collection.get(
                    where={"$and": where_conditions} if len(where_conditions) > 1 else where_conditions[0]
                )
            else:
                results = files_collection.get()
            
            # Filter for current only
            files = []
            for metadata in results['metadatas']:
                if current_only:
                    valid_until = metadata.get('valid_until')
                    # Current version has valid_until = None or empty string
                    if valid_until is None or valid_until == '':
                        files.append(metadata)
                else:
                    files.append(metadata)
            
            # Sort by ingested_at descending
            files = sorted(files, key=lambda x: x.get('ingested_at', ''), reverse=True)
            
            total_count = len(files)
            
            # Apply pagination
            paginated_files = files[offset:offset + limit]
            
            return paginated_files, total_count
        except Exception:
            return [], 0
    
    def get_chunks_by_file_id(self, file_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a specific file ID ordered by chunk_number."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            chunks_collection = self._client.get_collection('content_chunks')
            
            logger.debug(f"Searching for chunks with file_id: {file_id} (type: {type(file_id)})")
            
            # Query chunks by file_id (keep as integer to match stored type)
            results = chunks_collection.get(
                where={"file_id": file_id}
            )
            
            logger.debug(f"Found {len(results['ids'])} chunks for file_id {file_id}")
            
            # Convert ChromaDB format to list of dictionaries
            chunks = []
            for i, chunk_id in enumerate(results['ids']):
                chunk_data = {
                    'id': chunk_id,
                    'content': results['documents'][i] if i < len(results['documents']) else '',
                    'metadata': results['metadatas'][i] if i < len(results['metadatas']) else {},
                    'chunk_number': results['metadatas'][i].get('chunk_number', i) if i < len(results['metadatas']) else i,
                    'summary': results['metadatas'][i].get('summary', '') if i < len(results['metadatas']) else ''
                }
                chunks.append(chunk_data)
            
            # Sort by chunk_number
            chunks = sorted(chunks, key=lambda x: x.get('chunk_number', 0))
            
            return chunks
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting chunks for file ID {file_id}: {e}")
            return []
    
    def semantic_search(self, query_text: str, limit: int = 5,
                       content_type: Optional[str] = None,
                       threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on content chunks using embeddings."""
        import logging
        import sys
        import os
        logger = logging.getLogger(__name__)
        
        try:
            chunks_collection = self._client.get_collection('content_chunks')
            
            # Generate query embedding using the same embedding generator
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
            from server.utils import create_embedding
            
            query_embedding = create_embedding(query_text)
            
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Build where clause for filtering
            where_clause = None
            if content_type:
                where_clause = {"content_type": content_type}
            
            # Perform semantic search using ChromaDB's query method with embedding
            results = chunks_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            # Convert ChromaDB format to list of dictionaries
            search_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    # Calculate similarity from distance
                    # ChromaDB uses squared L2 distance by default (hnsw:space='l2')
                    # For normalized vectors: L2² = 2 * (1 - cosine_similarity)
                    # Therefore: cosine_similarity = 1 - (L2² / 2)
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    similarity = 1 - (distance / 2)  # Convert squared L2 distance to cosine similarity
                    
                    # Apply threshold filter if specified
                    if threshold is not None and similarity < threshold:
                        continue
                    
                    chunk_data = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i] if results.get('documents') else '',
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'similarity': similarity,
                        'distance': distance
                    }
                    
                    # Add common fields from metadata for easier access
                    metadata = chunk_data['metadata']
                    chunk_data['url'] = metadata.get('url', '')
                    chunk_data['chunk_number'] = metadata.get('chunk_number', 0)
                    chunk_data['summary'] = metadata.get('summary', '')
                    chunk_data['file_id'] = metadata.get('file_id', '')
                    
                    search_results.append(chunk_data)
            
            logger.info(f"Semantic search found {len(search_results)} results for query: {query_text[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            import traceback
            traceback.print_exc()
            return []
