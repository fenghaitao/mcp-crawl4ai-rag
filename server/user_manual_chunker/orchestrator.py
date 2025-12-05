"""
User Manual Chunker Orchestrator.

Main orchestrator that coordinates parsing, chunking, metadata extraction,
summary generation, and embedding generation for technical documentation.
"""

import os
import hashlib
import time
import json
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .interfaces import DocumentParser, DocumentChunk
from .data_models import DocumentStructure, ProcessedChunk, ChunkMetadata
from .config import ChunkerConfig
from .markdown_parser import MarkdownParser
from .html_parser import HTMLParser
from .semantic_chunker import SemanticChunker, PatternAwareSemanticChunker
from .metadata_extractor import MetadataExtractor
from .summary_generator import SummaryGenerator
from .embedding_generator import EmbeddingGenerator

# Set up logging
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


class UserManualChunker:
    """
    Main orchestrator for user manual chunking pipeline.
    
    Coordinates:
    - Document parsing (markdown/HTML)
    - Semantic chunking
    - Metadata extraction
    - Summary generation
    - Embedding generation
    - Statistics tracking
    """
    
    def __init__(
        self,
        parser: Optional[DocumentParser] = None,
        chunker: Optional[SemanticChunker] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        summary_generator: Optional[SummaryGenerator] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        config: Optional[ChunkerConfig] = None
    ):
        """
        Initialize the user manual chunker.
        
        Args:
            parser: Document parser (defaults to MarkdownParser)
            chunker: Semantic chunker (created from config if not provided)
            metadata_extractor: Metadata extractor (defaults to MetadataExtractor)
            summary_generator: Summary generator (created from config if not provided)
            embedding_generator: Embedding generator (created from config if not provided)
            config: Configuration object (defaults to ChunkerConfig.from_env())
        """
        # Load configuration
        self.config = config or ChunkerConfig.from_env()
        self.config.validate()
        
        # Initialize components with defaults if not provided
        self.parser = parser or MarkdownParser()
        self.chunker = chunker or PatternAwareSemanticChunker.from_config(self.config)
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        
        # Initialize optional components based on config
        if self.config.generate_summaries:
            self.summary_generator = summary_generator or SummaryGenerator(
                model=self.config.summary_model,
                max_summary_length=self.config.max_summary_length,
                timeout=self.config.summary_timeout_seconds
            )
        else:
            self.summary_generator = None
        
        if self.config.generate_embeddings:
            self.embedding_generator = embedding_generator or EmbeddingGenerator(
                model=self.config.embedding_model,
                batch_size=self.config.embedding_batch_size,
                normalize=True,
                max_retries=self.config.embedding_retry_attempts,
                initial_retry_delay=1.0,
                rate_limit_requests=self.config.copilot_requests_per_minute,
                rate_limit_window=60.0
            )
        else:
            self.embedding_generator = None
        
        # Statistics tracking
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_code_blocks": 0,
            "average_chunk_size": 0.0,
            "processing_time_seconds": 0.0,
            "failed_documents": 0
        }
    
    @classmethod
    def from_config(cls, config: ChunkerConfig) -> 'UserManualChunker':
        """
        Create UserManualChunker from configuration.
        
        Args:
            config: Configuration object
            
        Returns:
            UserManualChunker instance
        """
        return cls(config=config)
    
    def process_document(
        self,
        file_path: str,
        generate_embeddings: bool = True,
        generate_summaries: bool = True
    ) -> List[ProcessedChunk]:
        """
        Process a single document end-to-end.
        
        Args:
            file_path: Path to document file
            generate_embeddings: Whether to generate embeddings (overrides config)
            generate_summaries: Whether to generate summaries (overrides config)
            
        Returns:
            List of ProcessedChunk objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        start_time = time.time()
        
        logger.info(f"Processing document: {file_path}")
        
        # Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Determine parser based on file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext in ['.html', '.htm']:
            parser = HTMLParser()
        elif file_ext in ['.md', '.markdown']:
            parser = MarkdownParser()
        else:
            # Default to markdown parser
            parser = self.parser
        
        # Parse document
        logger.info("Parsing document structure...")
        doc_structure = parser.parse(content, source_path=file_path)
        
        # Chunk document
        logger.info("Chunking document...")
        chunks = self.chunker.chunk_document(doc_structure)
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Extract metadata for each chunk
        logger.info("Extracting metadata...")
        processed_chunks = []
        
        for chunk in chunks:
            # Extract metadata
            metadata = self.metadata_extractor.extract(chunk, doc_structure)
            
            # Generate unique chunk ID
            chunk_id = self._generate_chunk_id(file_path, chunk.chunk_index)
            
            # Create processed chunk
            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                content=chunk.content,
                metadata=metadata,
                summary=None,
                embedding=None
            )
            
            processed_chunks.append(processed_chunk)
        
        # Generate summaries if requested
        if generate_summaries and self.summary_generator:
            logger.info("Generating summaries...")
            doc_context = self._extract_document_context(doc_structure)
            
            for i, (chunk, processed_chunk) in enumerate(zip(chunks, processed_chunks)):
                try:
                    summary = self.summary_generator.generate_summary(
                        chunk,
                        doc_context,
                        processed_chunk.metadata
                    )
                    processed_chunk.summary = summary
                except Exception as e:
                    logger.error(f"Failed to generate summary for chunk {i}: {e}")
                    processed_chunk.summary = None
        
        # Generate embeddings if requested
        if generate_embeddings and self.embedding_generator:
            logger.info("Generating embeddings...")
            try:
                # Extract summaries from processed chunks
                summaries = [pc.summary for pc in processed_chunks]
                
                # Generate embeddings combining content + summary
                embeddings = self.embedding_generator.generate_embeddings(chunks, summaries)
                
                for processed_chunk, embedding in zip(processed_chunks, embeddings):
                    processed_chunk.embedding = embedding
                    
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
        
        # Update statistics
        processing_time = time.time() - start_time
        self._update_statistics(processed_chunks, processing_time)
        
        logger.info(f"Document processing complete in {processing_time:.2f}s")
        
        return processed_chunks
    
    def process_directory(
        self,
        directory: str,
        pattern: str = "*.md",
        recursive: bool = True
    ) -> List[ProcessedChunk]:
        """
        Process multiple documents in a directory.
        
        Args:
            directory: Path to directory containing documents
            pattern: Glob pattern for file matching (default: *.md)
            recursive: Whether to search recursively (default: True)
            
        Returns:
            List of all ProcessedChunk objects from all documents
            
        Raises:
            NotADirectoryError: If directory doesn't exist
        """
        logger.info(f"Processing directory: {directory}")
        logger.info(f"Pattern: {pattern}, Recursive: {recursive}")
        
        # Check directory exists
        dir_path = Path(directory)
        if not dir_path.exists():
            raise NotADirectoryError(f"Directory not found: {directory}")
        
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        # Find matching files
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
        
        logger.info(f"Found {len(files)} files matching pattern")
        
        # Process each file
        all_chunks = []
        
        for file_path in files:
            try:
                chunks = self.process_document(str(file_path))
                all_chunks.extend(chunks)
                self.stats["total_documents"] += 1
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                self.stats["failed_documents"] += 1
        
        logger.info(f"Directory processing complete: {len(all_chunks)} total chunks")
        
        return all_chunks
    
    def _generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """
        Generate unique chunk ID.
        
        Format: <file_hash>_<chunk_index>
        
        Args:
            file_path: Source file path
            chunk_index: Index of chunk in document
            
        Returns:
            Unique chunk ID string
        """
        # Create hash from file path
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:12]
        
        # Format: filehash_index
        chunk_id = f"{file_hash}_{chunk_index:04d}"
        
        return chunk_id
    
    def _extract_document_context(self, doc_structure: DocumentStructure) -> str:
        """
        Extract high-level context about the document.
        
        Uses the first heading or file name as context.
        
        Args:
            doc_structure: Document structure
            
        Returns:
            Context string
        """
        # Try to get first H1 heading
        for heading in doc_structure.headings:
            if heading.level == 1:
                return heading.text
        
        # Fall back to file name
        file_name = Path(doc_structure.source_path).stem
        return file_name.replace('_', ' ').replace('-', ' ').title()
    
    def _update_statistics(
        self,
        processed_chunks: List[ProcessedChunk],
        processing_time: float
    ) -> None:
        """
        Update processing statistics.
        
        Args:
            processed_chunks: List of processed chunks
            processing_time: Time taken to process in seconds
        """
        # Count chunks and code blocks
        num_chunks = len(processed_chunks)
        num_code_blocks = sum(
            1 for chunk in processed_chunks 
            if chunk.metadata.contains_code
        )
        
        # Calculate average chunk size
        if num_chunks > 0:
            total_chars = sum(chunk.metadata.char_count for chunk in processed_chunks)
            avg_size = total_chars / num_chunks
        else:
            avg_size = 0.0
        
        # Update cumulative statistics
        self.stats["total_chunks"] += num_chunks
        self.stats["total_code_blocks"] += num_code_blocks
        self.stats["processing_time_seconds"] += processing_time
        
        # Update average (weighted by total chunks)
        if self.stats["total_chunks"] > 0:
            self.stats["average_chunk_size"] = (
                (self.stats["average_chunk_size"] * (self.stats["total_chunks"] - num_chunks) +
                 avg_size * num_chunks) / self.stats["total_chunks"]
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_code_blocks": 0,
            "average_chunk_size": 0.0,
            "processing_time_seconds": 0.0,
            "failed_documents": 0
        }
    
    def export_to_json(
        self,
        chunks: List[ProcessedChunk],
        output_path: str,
        include_statistics: bool = True
    ) -> None:
        """
        Export chunks to JSON format.
        
        Handles numpy array serialization, checks disk space and permissions,
        and handles JSON serialization errors gracefully.
        
        Args:
            chunks: List of ProcessedChunk objects to export
            output_path: Path to output JSON file
            include_statistics: Whether to include processing statistics
            
        Raises:
            StorageError: If storage checks fail or file cannot be written
        """
        import json
        import numpy as np
        
        logger.info(f"Exporting {len(chunks)} chunks to {output_path}")
        
        # Validate output path
        output_path_obj = Path(output_path)
        
        # Check disk space before processing
        self._check_disk_space(output_path_obj)
        
        # Check write permissions
        self._check_write_permissions(output_path_obj)
        
        # Convert chunks to dictionaries with error handling
        chunks_data = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_dict = chunk.to_dict()
                chunks_data.append(chunk_dict)
            except Exception as e:
                logger.error(f"Failed to serialize chunk {i}: {e}")
                # Try to create a minimal representation
                try:
                    minimal_dict = {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                        "error": f"Serialization failed: {str(e)}"
                    }
                    chunks_data.append(minimal_dict)
                except Exception as e2:
                    logger.error(f"Failed to create minimal representation for chunk {i}: {e2}")
                    continue
        
        # Build output structure
        output_data = {
            "chunks": chunks_data
        }
        
        # Add statistics if requested
        if include_statistics:
            try:
                output_data["statistics"] = self.get_statistics()
            except Exception as e:
                logger.warning(f"Failed to add statistics: {e}")
        
        # Ensure output directory exists
        try:
            output_dir = output_path_obj.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create output directory: {e}")
        
        # Write to temporary file first, then rename (atomic operation)
        temp_path = output_path_obj.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, cls=NumpyEncoder)
            
            # Rename to final path (atomic on most systems)
            temp_path.replace(output_path_obj)
            
            logger.info(f"Successfully exported to {output_path}")
            
        except TypeError as e:
            # JSON serialization error
            logger.error(f"JSON serialization error: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to serialize data to JSON: {e}")
            
        except IOError as e:
            # File I/O error
            logger.error(f"File I/O error: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to write JSON file: {e}")
            
        except Exception as e:
            # Other errors
            logger.error(f"Unexpected error during export: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to export to JSON: {e}")
    
    def _check_disk_space(self, output_path: Path, required_mb: int = 100) -> None:
        """
        Check if sufficient disk space is available.
        
        Args:
            output_path: Path where file will be written
            required_mb: Required space in megabytes
            
        Raises:
            StorageError: If insufficient disk space
        """
        try:
            # Get disk usage statistics
            stat = shutil.disk_usage(output_path.parent if output_path.parent.exists() else Path.cwd())
            
            # Convert to MB
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < required_mb:
                raise StorageError(
                    f"Insufficient disk space: {free_mb:.1f}MB available, "
                    f"{required_mb}MB required"
                )
            
            logger.debug(f"Disk space check passed: {free_mb:.1f}MB available")
            
        except StorageError:
            raise
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            # Don't fail if we can't check - just warn
    
    def _check_write_permissions(self, output_path: Path) -> None:
        """
        Check if we have write permissions for the output path.
        
        Args:
            output_path: Path where file will be written
            
        Raises:
            StorageError: If write permissions are insufficient
        """
        try:
            # Check if file exists
            if output_path.exists():
                # Check if we can write to existing file
                if not os.access(output_path, os.W_OK):
                    raise StorageError(f"No write permission for existing file: {output_path}")
            else:
                # Check if we can write to parent directory
                parent_dir = output_path.parent
                
                # Create parent directory if it doesn't exist
                if not parent_dir.exists():
                    try:
                        parent_dir.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        raise StorageError(f"Cannot create output directory: {e}")
                
                # Check write permission on parent directory
                if not os.access(parent_dir, os.W_OK):
                    raise StorageError(f"No write permission for directory: {parent_dir}")
            
            logger.debug(f"Write permission check passed for {output_path}")
            
        except StorageError:
            raise
        except Exception as e:
            logger.warning(f"Could not check write permissions: {e}")
            # Don't fail if we can't check - just warn
    
    def export_to_vector_db_format(
        self,
        chunks: List[ProcessedChunk],
        output_path: str
    ) -> None:
        """
        Export chunks in vector database format.
        
        Format optimized for vector database ingestion with separate
        fields for content, metadata, and embeddings. Includes storage
        error handling.
        
        Args:
            chunks: List of ProcessedChunk objects to export
            output_path: Path to output JSON file
            
        Raises:
            StorageError: If storage checks fail or file cannot be written
        """
        import json
        
        logger.info(f"Exporting {len(chunks)} chunks to vector DB format: {output_path}")
        
        # Validate output path
        output_path_obj = Path(output_path)
        
        # Check disk space before processing
        self._check_disk_space(output_path_obj)
        
        # Check write permissions
        self._check_write_permissions(output_path_obj)
        
        # Convert to vector DB format with error handling
        vector_db_data = []
        
        for i, chunk in enumerate(chunks):
            try:
                record = {
                    "id": chunk.chunk_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata.to_dict(),
                    "summary": chunk.summary,
                    "embedding": chunk.embedding.tolist() if chunk.embedding is not None else None
                }
                vector_db_data.append(record)
            except Exception as e:
                logger.error(f"Failed to serialize chunk {i} for vector DB: {e}")
                # Try minimal representation
                try:
                    minimal_record = {
                        "id": chunk.chunk_id,
                        "content": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                        "error": f"Serialization failed: {str(e)}"
                    }
                    vector_db_data.append(minimal_record)
                except Exception as e2:
                    logger.error(f"Failed to create minimal record for chunk {i}: {e2}")
                    continue
        
        # Ensure output directory exists
        try:
            output_dir = output_path_obj.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(f"Failed to create output directory: {e}")
        
        # Write to temporary file first, then rename (atomic operation)
        temp_path = output_path_obj.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(vector_db_data, f, indent=2)
            
            # Rename to final path (atomic on most systems)
            temp_path.replace(output_path_obj)
            
            logger.info(f"Successfully exported to {output_path}")
            
        except TypeError as e:
            # JSON serialization error
            logger.error(f"JSON serialization error: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to serialize data to JSON: {e}")
            
        except IOError as e:
            # File I/O error
            logger.error(f"File I/O error: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to write JSON file: {e}")
            
        except Exception as e:
            # Other errors
            logger.error(f"Unexpected error during export: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(f"Failed to export to vector DB format: {e}")


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for numpy arrays and types.
    
    Handles serialization of numpy arrays to lists and numpy numeric types
    to Python native types.
    """
    
    def default(self, obj):
        """
        Convert numpy types to JSON-serializable types.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation
        """
        import numpy as np
        
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        
        return super().default(obj)
