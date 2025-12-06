"""
Document Ingest Service - Clean interface for document processing.

This service extracts the core document processing logic from 
chunk_user_manuals.py and integrates it with our backend architecture.
"""

import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..user_manual_chunker import UserManualChunker
from ..user_manual_chunker.config import ChunkerConfig


class DocumentIngestService:
    """Service for ingesting documentation files into the RAG system."""
    
    def __init__(self, backend):
        """Initialize with database backend."""
        self.backend = backend
        self._chunker = None
    
    def _get_chunker(self):
        """Get or create chunker instance."""
        if self._chunker is None:
            config = ChunkerConfig.from_env()
            self._chunker = UserManualChunker.from_config(config)
        return self._chunker
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics."""
        file_stat = Path(file_path).stat()
        return {
            'size': file_stat.st_size,
            'modified_time': file_stat.st_mtime
        }
    
    def _check_existing_file(self, file_path: str, content_hash: str) -> Optional[Dict]:
        """Check if file already exists in database with same hash."""
        try:
            if self.backend.get_backend_name() == 'supabase':
                result = self.backend._client.table('files').select('*').eq('file_path', file_path).eq('content_hash', content_hash).execute()
                if result.data:
                    return result.data[0]
            elif self.backend.get_backend_name() == 'chroma':
                # For ChromaDB, check files collection
                try:
                    files_collection = self.backend._client.get_collection('files')
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
                except Exception:
                    pass
            return None
        except Exception:
            return None
    
    def _remove_existing_file_data(self, file_path: str):
        """Remove existing file and its chunks from database."""
        try:
            if self.backend.get_backend_name() == 'supabase':
                # Get file record
                file_result = self.backend._client.table('files').select('id').eq('file_path', file_path).execute()
                if file_result.data:
                    file_id = file_result.data[0]['id']
                    
                    # Delete content_chunks first (foreign key constraint)
                    self.backend._client.table('content_chunks').delete().eq('file_id', file_id).execute()
                    
                    # Delete file record
                    self.backend._client.table('files').delete().eq('id', file_id).execute()
            # TODO: Add ChromaDB implementation
        except Exception as e:
            raise Exception(f"Failed to remove existing file data: {e}")
    
    def _store_file_record(self, file_path: str, content_hash: str, stats: Dict) -> str:
        """Store file record and return file ID."""
        try:
            if self.backend.get_backend_name() == 'supabase':
                file_data = {
                    'file_path': file_path,
                    'content_hash': content_hash,
                    'file_size': stats['size'],
                    'content_type': 'documentation',
                    'word_count': 0,
                    'chunk_count': 0
                }
                result = self.backend._client.table('files').insert(file_data).execute()
                return result.data[0]['id']
            elif self.backend.get_backend_name() == 'chroma':
                # For ChromaDB, use files collection
                files_collection = self.backend._client.get_or_create_collection('files')
                
                # Generate unique file ID
                file_id = f"file_{hashlib.md5(file_path.encode()).hexdigest()[:16]}"
                
                file_metadata = {
                    'file_path': file_path,
                    'content_hash': content_hash,
                    'file_size': stats['size'],
                    'content_type': 'documentation',
                    'word_count': 0,
                    'chunk_count': 0
                }
                
                files_collection.add(
                    ids=[file_id],
                    documents=[file_path],  # Use file path as document content
                    metadatas=[file_metadata]
                )
                return file_id
            else:
                raise NotImplementedError(f"Backend {self.backend.get_backend_name()} not supported")
        except Exception as e:
            raise Exception(f"Failed to store file record: {e}")
    
    def _store_chunks(self, file_id: str, chunks: list, file_path: str) -> Dict[str, int]:
        """Store chunks in database and return statistics."""
        try:
            total_chunks = 0
            total_words = 0
            
            if self.backend.get_backend_name() == 'supabase':
                chunk_records = []
                
                for i, chunk in enumerate(chunks):
                    # Convert ProcessedChunk to database record
                    chunk_data = {
                        'file_id': file_id,
                        'url': file_path,
                        'chunk_number': i,
                        'content': chunk.content,
                        'content_type': 'documentation',
                        'metadata': {
                            'title': chunk.metadata.heading_hierarchy[-1] if chunk.metadata.heading_hierarchy else '',
                            'section': ' > '.join(chunk.metadata.heading_hierarchy),
                            'heading_hierarchy': chunk.metadata.heading_hierarchy,
                            'word_count': chunk.metadata.char_count // 5,  # Rough word count estimate
                            'has_code': chunk.metadata.contains_code,
                            'language_hints': chunk.metadata.code_languages
                        },
                        'embedding': chunk.embedding if chunk.embedding else None
                    }
                    
                    chunk_records.append(chunk_data)
                    total_words += getattr(chunk.metadata, 'word_count', 0)
                
                total_chunks = len(chunk_records)
                
                # Batch insert chunks
                if chunk_records:
                    self.backend._client.table('content_chunks').insert(chunk_records).execute()
                
                # Update file record with statistics
                self.backend._client.table('files').update({
                    'word_count': total_words,
                    'chunk_count': total_chunks
                }).eq('id', file_id).execute()
                
            elif self.backend.get_backend_name() == 'chroma':
                # For ChromaDB, store in content_chunks collection
                chunks_collection = self.backend._client.get_or_create_collection('content_chunks')
                
                chunk_ids = []
                chunk_documents = []
                chunk_metadatas = []
                chunk_embeddings = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{file_id}_chunk_{i}"
                    chunk_ids.append(chunk_id)
                    chunk_documents.append(chunk.content)
                    
                    # Prepare metadata
                    metadata = {
                        'file_id': file_id,
                        'url': file_path,
                        'chunk_number': i,
                        'content_type': 'documentation',
                        'title': chunk.metadata.heading_hierarchy[-1] if chunk.metadata.heading_hierarchy else '',
                        'section': ' > '.join(chunk.metadata.heading_hierarchy),
                        'word_count': chunk.metadata.char_count // 5,  # Rough word count estimate  
                        'has_code': chunk.metadata.contains_code
                    }
                    chunk_metadatas.append(metadata)
                    
                    # Add embedding if available
                    if chunk.embedding is not None:
                        # Convert numpy array to list if needed
                        embedding = chunk.embedding
                        if hasattr(embedding, 'tolist'):
                            embedding = embedding.tolist()
                        chunk_embeddings.append(embedding)
                    
                    total_words += getattr(chunk.metadata, 'word_count', 0)
                
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
                
                # Update file record with statistics
                files_collection = self.backend._client.get_collection('files')
                files_collection.update(
                    ids=[file_id],
                    metadatas=[{
                        'file_path': file_path,
                        'content_type': 'documentation',
                        'word_count': total_words,
                        'chunk_count': total_chunks
                    }]
                )
                
            else:
                raise NotImplementedError(f"Backend {self.backend.get_backend_name()} not supported")
            
            return {'chunks': total_chunks, 'words': total_words}
            
        except Exception as e:
            raise Exception(f"Failed to store chunks: {e}")
    
    # Removed _ensure_source_exists - no longer needed for file-based workflow
    
    def ingest_document(self, file_path: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Ingest a single document file into the RAG system.
        
        Returns:
            Dict with success status, file_id, chunks_created, word_count, processing_time, error
        """
        start_time = time.time()
        
        try:
            # No longer need sources for file-based workflow
            
            # Calculate file hash for change detection
            content_hash = self._calculate_file_hash(file_path)
            file_stats = self._get_file_stats(file_path)
            
            # Check if file already processed (unless force)
            if not force_reprocess:
                existing = self._check_existing_file(file_path, content_hash)
                if existing:
                    return {
                        'success': True,
                        'file_id': existing['id'],
                        'chunks_created': existing['chunk_count'],
                        'word_count': existing['word_count'],
                        'processing_time': time.time() - start_time,
                        'skipped': True,
                        'reason': 'File already processed with same content'
                    }
            
            # Remove existing data if force reprocessing
            if force_reprocess:
                self._remove_existing_file_data(file_path)
            
            # Store file record
            file_id = self._store_file_record(file_path, content_hash, file_stats)
            
            # Process document with UserManualChunker
            chunker = self._get_chunker()
            chunks = chunker.process_document(
                file_path,
                generate_embeddings=True,
                generate_summaries=False  # Keep it simple for now
            )
            
            # Store chunks in database
            stats = self._store_chunks(file_id, chunks, file_path)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'file_id': file_id,
                'chunks_created': stats['chunks'],
                'word_count': stats['words'],
                'processing_time': processing_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }