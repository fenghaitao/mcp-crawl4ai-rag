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
    
    def _store_file_record(self, file_path: str, content_hash: str, stats: Dict) -> str:
        """Store file record and return file ID."""
        try:
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
        
        Returns:
            Dict with success status, file_id, chunks_created, word_count, processing_time, error
        """
        start_time = time.time()
        
        try:
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
            
            # Read settings from environment
            generate_summaries = os.getenv("MANUAL_GENERATE_SUMMARIES", "true").lower() == "true"
            
            chunks = chunker.process_document(
                file_path,
                generate_embeddings=True,
                generate_summaries=generate_summaries
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
