"""
Document Ingest Service - Clean interface for document processing.

This service extracts the core document processing logic from 
chunk_user_manuals.py and integrates it with our backend architecture.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from ..user_manual_chunker import UserManualChunker
from ..user_manual_chunker.config import ChunkerConfig

# Load environment variables
load_dotenv()


class DocumentIngestService:
    """Service for ingesting documentation files into the RAG system."""
    
    def __init__(self, backend, git_service=None):
        """Initialize with database backend and optional git service."""
        self.backend = backend
        self.git_service = git_service
        self._chunker = None
    
    def _get_chunker(self):
        """Get or create chunker instance."""
        if self._chunker is None:
            config = ChunkerConfig.from_env()
            self._chunker = UserManualChunker.from_config(config)
        return self._chunker
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content."""
        from ..cli.utils import calculate_file_hash
        return calculate_file_hash(file_path)
    
    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics."""
        file_stat = Path(file_path).stat()
        return {
            'size': file_stat.st_size,
            'modified_time': file_stat.st_mtime
        }
    
    def _check_existing_file(self, file_path: str, content_hash: str) -> Optional[Dict]:
        """Check if file already exists in database with same hash."""
        return self.backend.check_file_exists(file_path, content_hash)
    
    def _remove_existing_file_data(self, file_path: str):
        """Remove existing file and its chunks from database."""
        if not self.backend.remove_file_data(file_path):
            raise Exception(f"Failed to remove existing file data for: {file_path}")
    
    def _store_file_record(self, file_path: str, content_hash: str, stats: Dict, git_info=None) -> str:
        """Store file record and return file ID."""
        from datetime import datetime
        
        try:
            # If git_service is available and file is in a repo, use temporal versioning
            if git_info:
                # Get or create repository record
                repo = self.backend.get_repository(git_info.repo_url)
                if not repo:
                    repo_name = git_info.repo_url.split('/')[-1].replace('.git', '')
                    repo_id = self.backend.store_repository(git_info.repo_url, repo_name)
                else:
                    repo_id = repo['id']
                    self.backend.update_repository_last_ingested(repo_id)
                
                # Convert file_path to absolute path and get relative path from git info
                abs_file_path = Path(file_path).resolve()
                relative_path = git_info.get_relative_path(abs_file_path)
                
                # Store file version with temporal fields
                file_version = {
                    'repo_id': repo_id,
                    'commit_sha': git_info.commit_sha,
                    'file_path': relative_path,
                    'content_hash': content_hash,
                    'file_size': stats['size'],
                    'word_count': 0,
                    'chunk_count': 0,
                    'content_type': 'documentation',
                    'valid_from': git_info.commit_timestamp,
                    'valid_until': None,
                    'ingested_at': datetime.now()
                }
                return self.backend.store_file_version(file_version)
            else:
                # Fall back to legacy method for files outside git repos
                return self.backend.store_file_record(
                    file_path=file_path,
                    content_hash=content_hash,
                    file_size=stats['size'],
                    content_type='documentation'
                )
        except Exception as e:
            raise Exception(f"Failed to store file record: {e}")
    
    def _store_chunks(self, file_id: str, chunks: list, file_path: str) -> Dict[str, int]:
        """Store chunks in database and return statistics."""
        try:
            # Store chunks using backend interface
            stats = self.backend.store_chunks(file_id, chunks, file_path)
            
            # Update file statistics using backend interface
            self.backend.update_file_statistics(file_id, stats['chunks'], stats['words'])
            
            return stats
            
        except Exception as e:
            raise Exception(f"Failed to store chunks: {e}")
    
    def ingest_document(self, file_path: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Ingest a single document file into the RAG system.
        
        Content-based versioning: Only creates new versions when content actually changes.
        - Without force: Skips if content unchanged
        - With force: Re-processes chunks (regenerates summaries/embeddings)
        
        Returns:
            Dict with success status, file_id, chunks_created, word_count, processing_time, error
        """
        start_time = time.time()
        
        try:
            # Check for uncommitted changes if git_service is available
            if self.git_service:
                is_committed, message = self.git_service.check_file_committed(Path(file_path))
                if not is_committed:
                    return {
                        'success': False,
                        'error': f'Cannot ingest file with uncommitted changes: {message}',
                        'processing_time': time.time() - start_time
                    }
            
            # Detect git repository if git_service is available
            git_info = None
            repo_id = None
            relative_path = file_path
            
            if self.git_service:
                git_info = self.git_service.detect_repository(Path(file_path))
                if git_info:
                    # Get or create repository record
                    repo = self.backend.get_repository(git_info.repo_url)
                    if not repo:
                        repo_name = git_info.repo_url.split('/')[-1].replace('.git', '')
                        repo_id = self.backend.store_repository(git_info.repo_url, repo_name)
                    else:
                        repo_id = repo['id']
                        self.backend.update_repository_last_ingested(repo_id)
                    
                    # Get relative path from git root
                    abs_file_path = Path(file_path).resolve()
                    relative_path = git_info.get_relative_path(abs_file_path)
            
            # Calculate file hash for change detection
            content_hash = self._calculate_file_hash(file_path)
            file_stats = self._get_file_stats(file_path)
            
            # Check for existing version with same content (content-based versioning)
            existing_current = None
            if git_info and repo_id:
                # For git-tracked files, check current version by repo_id and path
                existing_current = self.backend.get_current_file(repo_id, relative_path)
            else:
                # For non-git files, check by file path and hash
                existing_current = self._check_existing_file(file_path, content_hash)
            
            # Content-based versioning logic
            if existing_current and existing_current.get('content_hash') == content_hash:
                # Content unchanged!
                if force_reprocess:
                    # Force: Re-process chunks (regenerate summaries/embeddings)
                    # Keep the same file_id but regenerate chunks
                    file_id = existing_current['id']
                    
                    # Remove old chunks only (not the file record)
                    try:
                        # Get chunks collection and remove chunks for this file
                        chunks_collection = self.backend._client.get_or_create_collection('content_chunks')
                        chunk_results = chunks_collection.get(where={"file_id": str(file_id)})
                        if chunk_results['ids']:
                            chunks_collection.delete(ids=chunk_results['ids'])
                    except Exception:
                        # If chunk removal fails, continue anyway
                        pass
                    
                    # Process document with UserManualChunker
                    chunker = self._get_chunker()
                    generate_summaries = os.getenv("MANUAL_GENERATE_SUMMARIES", "true").lower() == "true"
                    
                    chunks = chunker.process_document(
                        file_path,
                        generate_embeddings=True,
                        generate_summaries=generate_summaries
                    )
                    
                    # Store new chunks
                    stats = self._store_chunks(file_id, chunks, relative_path if git_info else file_path)
                    
                    processing_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'file_id': file_id,
                        'chunks_created': stats['chunks'],
                        'word_count': stats['words'],
                        'processing_time': processing_time,
                        'reprocessed': True,
                        'reason': 'Content unchanged - re-processed with force flag'
                    }
                else:
                    # No force: Skip entirely
                    return {
                        'success': True,
                        'file_id': existing_current['id'],
                        'chunks_created': existing_current.get('chunk_count', 0),
                        'word_count': existing_current.get('word_count', 0),
                        'processing_time': time.time() - start_time,
                        'skipped': True,
                        'reason': 'Content unchanged - skipped'
                    }
            
            # Content changed or new file: Create new version
            # DO NOT remove existing data - temporal versioning keeps all versions
            
            # Store file record (with git info if available)
            file_id = self._store_file_record(file_path, content_hash, file_stats, git_info)
            
            # Process document with UserManualChunker
            chunker = self._get_chunker()
            generate_summaries = os.getenv("MANUAL_GENERATE_SUMMARIES", "true").lower() == "true"
            
            chunks = chunker.process_document(
                file_path,
                generate_embeddings=True,
                generate_summaries=generate_summaries
            )
            
            # Store chunks in database
            stats = self._store_chunks(file_id, chunks, relative_path if git_info else file_path)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'file_id': file_id,
                'chunks_created': stats['chunks'],
                'word_count': stats['words'],
                'processing_time': processing_time,
                'new_version': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
