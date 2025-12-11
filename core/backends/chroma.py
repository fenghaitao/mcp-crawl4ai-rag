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
        
        For the 'content_chunks' collection, if hybrid search is enabled, this method
        will set up BM25 sparse indexing in addition to dense vector embeddings.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Check if this is the content_chunks collection and hybrid search is enabled
            if name == 'content_chunks' and self._is_hybrid_search_enabled():
                logger.info(f"Hybrid search is enabled for collection '{name}'")
                
                # Attempt to set up hybrid collection with BM25 support
                collection = self._setup_hybrid_collection(name)
                
                # If BM25 setup failed, fall back to standard collection
                if collection is None:
                    logger.warning(f"BM25 setup failed for '{name}', using standard collection")
                    collection = self._client.get_or_create_collection(
                        name=name,
                        metadata={"hnsw:space": "cosine"}
                    )
                
                return collection
            else:
                # For other collections or when hybrid search is disabled
                if name == 'content_chunks':
                    logger.info(f"Hybrid search is disabled for collection '{name}', using dense-only search")
                
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
                    # Use _get_or_create_metadata_collection to ensure proper setup
                    # (including hybrid search for content_chunks if enabled)
                    collection = self._get_or_create_metadata_collection(collection_name)
                    print(f"✅ Collection '{collection_name}' ready")
                except Exception as create_error:
                    print(f"❌ Error setting up collection '{collection_name}': {create_error}")
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
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get all file records matching this path
            files_collection = self._client.get_collection('files')
            file_results = files_collection.get(
                where={"file_path": file_path}
            )
            
            if file_results['ids']:
                logger.info(f"Found {len(file_results['ids'])} file record(s) for path: {file_path}")
                
                # Remove chunks for all file versions
                try:
                    chunks_collection = self._client.get_collection('content_chunks')
                    total_chunks_removed = 0
                    
                    for i, file_id in enumerate(file_results['ids']):
                        # Get the actual file_id from metadata to ensure consistency
                        file_metadata = file_results['metadatas'][i]
                        actual_file_id = file_metadata.get('id', file_id)
                        
                        # Try both string and integer versions for compatibility
                        for search_id in [actual_file_id, str(actual_file_id), int(actual_file_id) if str(actual_file_id).isdigit() else None]:
                            if search_id is None:
                                continue
                                
                            chunk_results = chunks_collection.get(
                                where={"file_id": search_id}
                            )
                            if chunk_results['ids']:
                                logger.info(f"Removing {len(chunk_results['ids'])} chunks for file_id: {search_id}")
                                chunks_collection.delete(ids=chunk_results['ids'])
                                total_chunks_removed += len(chunk_results['ids'])
                                break  # Found chunks, don't try other ID formats
                    
                    logger.info(f"Total chunks removed: {total_chunks_removed}")
                    
                except Exception as e:
                    # Log but don't fail - collection might not exist or have no chunks
                    logger.warning(f"Error removing chunks for {file_path}: {e}")
                
                # Remove all file records
                files_collection.delete(ids=file_results['ids'])
                logger.info(f"Removed {len(file_results['ids'])} file record(s)")
            else:
                logger.info(f"No file records found for path: {file_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error removing file data for {file_path}: {e}")
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
        chunks_collection = self._get_or_create_metadata_collection('content_chunks')
        
        chunk_ids = []
        chunk_contents = []
        chunk_metadatas = []
        chunk_embeddings = []
        total_words = 0
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # Safely get content (handle None)
            content = chunk.content if chunk.content else ''
            chunk_contents.append(content)
            
            # Prepare metadata - safely access attributes that may not exist
            char_count = getattr(chunk.metadata, 'char_count', len(content))
            word_count = char_count // 5  # Rough word count estimate
            
            # Get content_type from metadata or default to 'documentation'
            content_type = getattr(chunk.metadata, 'content_type', 'documentation')
            
            # Get source_id if available (for source code files)
            source_id = getattr(chunk.metadata, 'source_id', '')
            
            # Get heading hierarchy safely
            heading_hierarchy = getattr(chunk.metadata, 'heading_hierarchy', [])
            
            # Get code-related attributes safely
            contains_code = getattr(chunk.metadata, 'contains_code', False)
            code_languages = getattr(chunk.metadata, 'code_languages', [])
            
            metadata = {
                'file_id': file_id,
                'url': file_path,
                'chunk_number': i,
                'content_type': content_type,
                'summary': chunk.summary if chunk.summary else '',
                'title': heading_hierarchy[-1] if heading_hierarchy else '',
                'section': ' > '.join(heading_hierarchy),
                'word_count': word_count,
                'has_code': contains_code,
                'heading_hierarchy': ' > '.join(heading_hierarchy),  # Convert list to string
                'language_hints': ', '.join(code_languages) if code_languages else '',  # Convert list to string
                'source_id': source_id  # Add source_id for filtering
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
                    documents=chunk_contents,
                    metadatas=chunk_metadatas,
                    embeddings=chunk_embeddings
                )
            else:
                chunks_collection.add(
                    ids=chunk_ids,
                    documents=chunk_contents,
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
    
    def _is_hybrid_search_enabled(self) -> bool:
        """Check if hybrid search is enabled via environment variable.
        
        Returns:
            bool: True if USE_HYBRID_SEARCH is set to a truthy value (true, 1, yes),
                  False otherwise.
        """
        use_hybrid = os.getenv('USE_HYBRID_SEARCH', '').lower()
        return use_hybrid in ('true', '1', 'yes')
    
    def _setup_hybrid_collection(self, collection_name: str):
        """Set up collection with BM25 sparse indexing support.
        
        This method configures a ChromaDB collection with both dense vector embeddings
        and sparse BM25 indexing for hybrid search capabilities.
        
        Args:
            collection_name: Name of the collection to create with hybrid search support
            
        Returns:
            ChromaDB collection object with hybrid search schema, or None if BM25 is not available
            
        Raises:
            Exception: If collection creation fails for reasons other than BM25 unavailability
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Import BM25 components
            from chromadb import Schema, K
            from chromadb.utils.embedding_functions import ChromaBm25EmbeddingFunction
            
            logger.info(f"Setting up hybrid collection '{collection_name}' with BM25 support")
            
            # Initialize BM25 embedding function
            bm25_ef = ChromaBm25EmbeddingFunction()
            
            # Define schema with sparse index
            schema = Schema()
            schema.create_index(
                key='bm25_sparse_vector',
                config={
                    'embedding_function': bm25_ef,
                    'source_key': K.DOCUMENT
                }
            )
            
            # Create collection with hybrid search schema
            collection = self._client.get_or_create_collection(
                name=collection_name,
                schema=schema,
                metadata={"hnsw:space": "cosine"}  # For dense vectors
            )
            
            logger.info(f"Successfully created hybrid collection '{collection_name}'")
            return collection
            
        except ImportError as e:
            # BM25 not available in this ChromaDB version
            logger.warning(f"BM25 not available in ChromaDB version, falling back to dense-only search: {e}")
            return None
        except AttributeError as e:
            # Schema or K not available
            logger.warning(f"BM25 schema components not available, falling back to dense-only search: {e}")
            return None
        except Exception as e:
            # Other errors during collection creation (e.g., missing dependencies like fastembed)
            logger.error(f"Error creating hybrid collection '{collection_name}': {e}")
            logger.warning("Falling back to dense-only search")
            return None

    def _perform_dense_search(self, query_embedding: List[float], 
                             limit: int, where_clause: Optional[Dict]) -> List[Dict[str, Any]]:
        """Perform dense vector search using query embedding.
        
        This method performs a semantic search using dense vector embeddings.
        It queries the ChromaDB collection using the provided embedding and returns
        results with similarity scores.
        
        Args:
            query_embedding: The embedding vector for the query
            limit: Maximum number of results to return
            where_clause: Optional filter conditions for the search
            
        Returns:
            List of dictionaries containing search results with similarity scores
            
        Raises:
            Exception: If the search operation fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            chunks_collection = self._client.get_collection('content_chunks')
            
            logger.debug(f"Performing dense search with limit={limit}, where_clause={where_clause}")
            
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
            
            logger.info(f"Dense search found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing dense search: {e}", exc_info=True)
            raise

    def _perform_sparse_search(self, query_text: str, 
                              limit: int, where_clause: Optional[Dict]) -> List[Dict[str, Any]]:
        """Perform BM25 sparse search using query text.
        
        This method performs a keyword-based search using BM25 sparse vectors.
        It queries the ChromaDB collection using the BM25 index and returns
        results with BM25 scores.
        
        Args:
            query_text: The text query for BM25 search
            limit: Maximum number of results to return
            where_clause: Optional filter conditions for the search
            
        Returns:
            List of dictionaries containing search results with BM25 scores
            
        Raises:
            Exception: If the search operation fails
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            chunks_collection = self._client.get_collection('content_chunks')
            
            logger.debug(f"Performing sparse BM25 search with limit={limit}, where_clause={where_clause}")
            
            # Perform BM25 search using ChromaDB's search API
            # The search method uses the BM25 sparse vectors configured in the schema
            results = chunks_collection.search(
                query_texts=[query_text],
                n_results=limit,
                where=where_clause
            )
            
            # Convert ChromaDB format to list of dictionaries
            search_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    # Get BM25 score from distances
                    # For BM25, higher scores are better, but ChromaDB returns distances
                    # We'll use the inverse of distance as the score
                    distance = results['distances'][0][i] if results.get('distances') else 0
                    bm25_score = 1 / (1 + distance) if distance >= 0 else 0
                    
                    chunk_data = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i] if results.get('documents') else '',
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'bm25_score': bm25_score,
                        'distance': distance
                    }
                    
                    # Add common fields from metadata for easier access
                    metadata = chunk_data['metadata']
                    chunk_data['url'] = metadata.get('url', '')
                    chunk_data['chunk_number'] = metadata.get('chunk_number', 0)
                    chunk_data['summary'] = metadata.get('summary', '')
                    chunk_data['file_id'] = metadata.get('file_id', '')
                    
                    search_results.append(chunk_data)
            
            logger.info(f"Sparse BM25 search found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing sparse BM25 search: {e}", exc_info=True)
            raise

    def _merge_results_with_rrf(self, dense_results: List[Dict[str, Any]], 
                                sparse_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """Merge search results using Reciprocal Rank Fusion (RRF).
        
        This method combines results from dense and sparse searches using the RRF algorithm.
        For each document, the RRF score is calculated as: sum(1 / (k + rank)) across all
        retrieval methods where the document appears.
        
        Args:
            dense_results: Results from dense vector search
            sparse_results: Results from sparse BM25 search
            k: RRF constant (default 60)
            
        Returns:
            List of merged results sorted by RRF score in descending order
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Merging {len(dense_results)} dense results with {len(sparse_results)} sparse results using RRF (k={k})")
            
            # Build a dictionary to track documents and their rankings
            doc_scores = {}
            
            # Process dense results
            for rank, result in enumerate(dense_results):
                doc_id = result['id']
                rrf_contribution = 1 / (k + rank + 1)  # rank is 0-indexed, so add 1
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'result': result,
                        'rrf_score': 0,
                        'dense_rank': None,
                        'sparse_rank': None
                    }
                
                doc_scores[doc_id]['rrf_score'] += rrf_contribution
                doc_scores[doc_id]['dense_rank'] = rank + 1  # Store 1-indexed rank
            
            # Process sparse results
            for rank, result in enumerate(sparse_results):
                doc_id = result['id']
                rrf_contribution = 1 / (k + rank + 1)  # rank is 0-indexed, so add 1
                
                if doc_id not in doc_scores:
                    # Document only in sparse results, need to get full data
                    doc_scores[doc_id] = {
                        'result': result,
                        'rrf_score': 0,
                        'dense_rank': None,
                        'sparse_rank': None
                    }
                
                doc_scores[doc_id]['rrf_score'] += rrf_contribution
                doc_scores[doc_id]['sparse_rank'] = rank + 1  # Store 1-indexed rank
            
            # Build merged results list
            merged_results = []
            for doc_id, doc_data in doc_scores.items():
                result = doc_data['result'].copy()
                result['rrf_score'] = doc_data['rrf_score']
                result['dense_rank'] = doc_data['dense_rank']
                result['sparse_rank'] = doc_data['sparse_rank']
                merged_results.append(result)
            
            # Sort by RRF score in descending order
            merged_results.sort(key=lambda x: x['rrf_score'], reverse=True)
            
            logger.info(f"RRF merging produced {len(merged_results)} unique documents")
            logger.debug(f"Top 3 RRF scores: {[r['rrf_score'] for r in merged_results[:3]]}")
            
            return merged_results
            
        except Exception as e:
            logger.error(f"Error merging results with RRF: {e}", exc_info=True)
            raise

    def _apply_threshold_and_limit(self, results: List[Dict[str, Any]], 
                                   threshold: Optional[float], limit: int) -> List[Dict[str, Any]]:
        """Apply threshold filtering and limit to search results.
        
        This method filters results by similarity threshold (if specified) and limits
        the number of results returned. It ensures all results contain required fields.
        
        Args:
            results: List of search results to filter
            threshold: Optional minimum similarity threshold (0-1)
            limit: Maximum number of results to return
            
        Returns:
            Filtered and limited list of results
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Applying threshold={threshold} and limit={limit} to {len(results)} results")
            
            filtered_results = results
            
            # Apply threshold filter if specified
            if threshold is not None:
                filtered_results = [
                    r for r in filtered_results 
                    if r.get('similarity', 0) >= threshold
                ]
                logger.debug(f"After threshold filtering: {len(filtered_results)} results")
            
            # Apply limit
            limited_results = filtered_results[:limit]
            
            # Ensure all results contain required fields
            for result in limited_results:
                # Ensure similarity field exists (for backward compatibility)
                if 'similarity' not in result:
                    result['similarity'] = 0.0
                
                # Ensure rrf_score exists in hybrid mode
                if 'rrf_score' not in result:
                    result['rrf_score'] = None
            
            logger.info(f"Returning {len(limited_results)} results after filtering and limiting")
            
            return limited_results
            
        except Exception as e:
            logger.error(f"Error applying threshold and limit: {e}", exc_info=True)
            raise

    def semantic_search(self, query_text: str, limit: int = 5,
                       content_type: Optional[str] = None,
                       threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on content chunks using embeddings.
        
        This method supports both dense-only and hybrid search modes. When hybrid search
        is enabled (USE_HYBRID_SEARCH=true), it performs both dense vector search and
        sparse BM25 search, then merges results using Reciprocal Rank Fusion (RRF).
        
        Args:
            query_text: The search query text
            limit: Maximum number of results to return (default 5)
            content_type: Optional filter by content type
            threshold: Optional minimum similarity threshold (0-1)
            
        Returns:
            List of search results with similarity scores and metadata
        """
        import logging
        import sys
        import os
        logger = logging.getLogger(__name__)
        
        try:
            # Input validation
            if not query_text or query_text.strip() == '':
                logger.warning("Empty query text provided")
                return []
            
            if limit < 1:
                logger.warning(f"Invalid limit {limit}, using default 5")
                limit = 5
            
            # Build where clause for filtering
            where_clause = None
            if content_type:
                where_clause = {"content_type": content_type}
            
            # Check if hybrid search is enabled
            if not self._is_hybrid_search_enabled():
                logger.debug("Hybrid search disabled, using dense-only search")
                
                # Generate query embedding
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from server.utils import create_embedding
                
                query_embedding = create_embedding(query_text)
                
                if query_embedding is None:
                    logger.error("Failed to generate query embedding")
                    return []
                
                # Perform dense-only search
                search_results = self._perform_dense_search(query_embedding, limit, where_clause)
                
                # Apply threshold and limit
                search_results = self._apply_threshold_and_limit(search_results, threshold, limit)
                
                logger.info(f"Dense-only search found {len(search_results)} results")
                return search_results
            
            # Hybrid search mode
            logger.info("Hybrid search enabled, performing dual search")
            
            dense_results = []
            sparse_results = []
            
            # Perform dense search
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from server.utils import create_embedding
                
                query_embedding = create_embedding(query_text)
                
                if query_embedding is not None:
                    # Request 2x limit to ensure sufficient candidates for merging
                    dense_limit = limit * 2
                    dense_results = self._perform_dense_search(query_embedding, dense_limit, where_clause)
                    logger.info(f"Dense search returned {len(dense_results)} results")
                else:
                    logger.warning("Failed to generate query embedding for dense search")
            except Exception as e:
                logger.error(f"Dense search failed: {e}", exc_info=True)
            
            # Perform sparse search
            try:
                # Request 2x limit to ensure sufficient candidates for merging
                sparse_limit = limit * 2
                sparse_results = self._perform_sparse_search(query_text, sparse_limit, where_clause)
                logger.info(f"Sparse search returned {len(sparse_results)} results")
            except Exception as e:
                logger.error(f"Sparse search failed: {e}", exc_info=True)
            
            # Handle partial failures
            if not dense_results and not sparse_results:
                logger.error("Both search methods failed")
                return []
            
            if not dense_results:
                logger.warning("Dense search failed, using sparse-only results")
                search_results = self._apply_threshold_and_limit(sparse_results, threshold, limit)
                logger.info(f"Returning {len(search_results)} sparse-only results")
                return search_results
            
            if not sparse_results:
                logger.warning("Sparse search failed, using dense-only results")
                search_results = self._apply_threshold_and_limit(dense_results, threshold, limit)
                logger.info(f"Returning {len(search_results)} dense-only results")
                return search_results
            
            # Merge results using RRF
            logger.debug("Merging dense and sparse results with RRF")
            merged_results = self._merge_results_with_rrf(dense_results, sparse_results)
            
            # Apply threshold and limit
            final_results = self._apply_threshold_and_limit(merged_results, threshold, limit)
            
            logger.info(f"Hybrid search completed: {len(final_results)} results returned")
            logger.debug(f"Result breakdown - Dense: {len(dense_results)}, Sparse: {len(sparse_results)}, Merged: {len(merged_results)}, Final: {len(final_results)}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}", exc_info=True)
            return []

    def cleanup_orphaned_chunks(self, dry_run: bool = False) -> Dict[str, Any]:
        """Find and optionally remove orphaned chunks that have no corresponding file records."""
        try:
            chunks_collection = self._client.get_collection('content_chunks')
            files_collection = self._client.get_collection('files')
            
            all_chunks = chunks_collection.get()
            all_files = files_collection.get()
            
            # Get valid file IDs
            valid_file_ids = set()
            for metadata in all_files['metadatas']:
                file_id = metadata.get('id')
                if file_id:
                    valid_file_ids.add(str(file_id))
            
            # Find orphaned chunks
            orphaned_chunk_ids = []
            orphan_groups = {}
            
            for i, chunk_id in enumerate(all_chunks['ids']):
                metadata = all_chunks['metadatas'][i]
                file_id = str(metadata.get('file_id', ''))
                url = metadata.get('url', 'Unknown')
                
                if file_id not in valid_file_ids:
                    orphaned_chunk_ids.append(chunk_id)
                    
                    if file_id not in orphan_groups:
                        orphan_groups[file_id] = {'count': 0, 'url': url, 'chunk_ids': []}
                    orphan_groups[file_id]['count'] += 1
                    orphan_groups[file_id]['chunk_ids'].append(chunk_id)
            
            result = {
                'total_chunks': len(all_chunks['ids']),
                'valid_files': len(valid_file_ids),
                'orphaned_chunks': len(orphaned_chunk_ids),
                'orphan_groups': orphan_groups,
                'removed': 0
            }
            
            # Perform cleanup if not dry run
            if not dry_run and orphaned_chunk_ids:
                chunks_collection.delete(ids=orphaned_chunk_ids)
                result['removed'] = len(orphaned_chunk_ids)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error during ChromaDB orphan cleanup: {e}")
