"""
Source Code Ingest Service - DML and Python file processing.

This service handles ingesting DML and Python source files into the RAG system,
extracting from crawl_simics_source.py and integrating with backend architecture.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add server to path for embedding utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))


class ChunkWithEmbedding:
    """Simple data class to hold chunk data for storage."""
    def __init__(self, content: str, metadata: Dict[str, Any], embedding: List[float] = None, summary: str = None):
        self.content = content
        self.metadata = SimpleMetadata(metadata)
        self.embedding = embedding
        self.summary = summary


class SimpleMetadata:
    """Simple metadata wrapper for chunks."""
    def __init__(self, metadata_dict: Dict[str, Any]):
        self._data = metadata_dict
        # Calculate char_count from content if not provided
        self.char_count = metadata_dict.get('char_count', len(metadata_dict.get('content', '')))
        self.heading_hierarchy = metadata_dict.get('heading_hierarchy', [])
        self.contains_code = metadata_dict.get('has_code', False)
        self.code_languages = metadata_dict.get('language_hints', [])
    
    def __getattr__(self, name):
        return self._data.get(name)


class SourceIngestService:
    """Service for ingesting source code files (DML, Python) into the RAG system."""
    
    def __init__(self, backend, source_type: str, git_service=None, test_filter: Optional[str] = None):
        """
        Initialize with database backend, source type, and optional git service.
        
        Args:
            backend: Database backend instance
            source_type: Type of source files ('dml', 'python', 'cpp')
            git_service: Optional GitService for version tracking
            test_filter: Test file filtering ('test-only', 'skip-test', or None)
        """
        self.backend = backend
        self.source_type = source_type.lower()
        self.git_service = git_service
        self.test_filter = test_filter
    
    def should_skip_file(self, file_path: str) -> bool:
        """
        Check if a file should be skipped during ingestion.
        
        Currently skips:
        - DML 1.2 files (older syntax not supported)
        - Python files based on test_filter setting:
          * test-only: Skip files NOT in test/tests folder or NOT starting with s-/test_
          * skip-test: Skip files IN test/tests folder or starting with s-/test_
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be skipped, False otherwise
        """
        path = Path(file_path)
        
        # Check if it's a DML file based on source_type
        if self.source_type == 'dml':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return self.is_dml_1_2(content)
            except Exception as e:
                logging.warning(f"Error reading file {file_path}: {e}")
                return False
        
        # Check Python test filtering
        if self.source_type == 'python' and self.test_filter:
            is_test_file = self._is_test_file(path)
            
            if self.test_filter == 'test-only':
                # Skip non-test files
                return not is_test_file
            elif self.test_filter == 'skip-test':
                # Skip test files
                return is_test_file
        
        return False
    
    def _is_test_file(self, path: Path) -> bool:
        """
        Determine if a Python file is a test file.
        
        A file is considered a test file if:
        - It's in a directory named 'test' or 'tests'
        - Its filename starts with 's-' or 'test_'
        
        Args:
            path: Path object for the file
            
        Returns:
            True if it's a test file, False otherwise
        """
        # Check if in test/tests directory
        parts = path.parts
        if any(part.lower() in ('test', 'tests') for part in parts):
            return True
        
        # Check if filename starts with s- or test_
        filename = path.name
        if filename.startswith('s-') or filename.startswith('test_'):
            return True
        
        return False
    
    def is_dml_1_2(self, content: str) -> bool:
        r"""
        Check if a DML file is version 1.2.
        
        DML 1.2 files are skipped as they use older syntax.
        Pattern matches: ^dml 1.2\s*;
        
        Args:
            content: File content
            
        Returns:
            True if DML 1.2, False otherwise
        """
        pattern = re.compile(r'^dml 1\.2\s*;', re.MULTILINE)
        return pattern.search(content) is not None
    
    def extract_dml_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Extract DML-specific metadata from source code.
        
        Extracts:
        - Device name
        - Templates (is statements)
        - Interfaces (implement statements)
        - Register groups
        - Methods
        - Basic statistics
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'file_path': file_path,
            'file_type': 'dml',
            'language': 'dml'
        }
        
        # Extract device name
        device_match = re.search(r'device\s+(\w+)', content)
        if device_match:
            metadata['device_name'] = device_match.group(1)
        
        # Extract templates (is template_name)
        template_matches = re.findall(r'is\s+(\w+)', content)
        if template_matches:
            metadata['templates'] = list(set(template_matches))
        
        # Extract interfaces (implement interface_name)
        interface_matches = re.findall(r'implement\s+(\w+)', content)
        if interface_matches:
            metadata['interfaces'] = list(set(interface_matches))
        
        # Extract register groups
        register_matches = re.findall(r'group\s+(\w+)', content)
        if register_matches:
            metadata['register_groups'] = list(set(register_matches))
        
        # Extract methods
        method_matches = re.findall(r'method\s+(\w+)', content)
        if method_matches:
            metadata['methods'] = list(set(method_matches))
        
        # Calculate basic stats
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        
        return metadata
    
    def extract_python_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Extract Python-specific metadata from source code.
        
        Extracts:
        - Classes
        - Functions
        - Simics imports
        - Device implementation detection
        - Basic statistics
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'file_path': file_path,
            'file_type': 'python',
            'language': 'python'
        }
        
        # Extract class definitions
        class_matches = re.findall(r'class\s+(\w+)', content)
        if class_matches:
            metadata['classes'] = list(set(class_matches))
        
        # Extract function definitions
        function_matches = re.findall(r'def\s+(\w+)', content)
        if function_matches:
            metadata['functions'] = list(set(function_matches))
        
        # Extract Simics imports
        simics_imports = re.findall(r'import\s+(simics\S*)', content)
        simics_from_imports = re.findall(r'from\s+(simics\S*)', content)
        all_simics_imports = simics_imports + simics_from_imports
        if all_simics_imports:
            metadata['simics_imports'] = list(set(all_simics_imports))
        
        # Check if it's a device Python file
        if 'simics' in content and ('device' in content.lower() or 'component' in content.lower()):
            metadata['is_device_implementation'] = True
        else:
            metadata['is_device_implementation'] = False
        
        # Calculate basic stats
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        
        return metadata
    
    def determine_source_id(self, file_type: str) -> str:
        """
        Determine source_id based on file type.
        
        Args:
            file_type: 'dml', 'python', 'cpp', etc.
            
        Returns:
            Source ID string (e.g., 'simics-dml')
        """
        if file_type == 'dml':
            return "simics-dml"
        elif file_type == 'python':
            return "simics-python"
        elif file_type == 'cpp':
            return "simics-cc"
        else:
            return "simics-source"
    
    def process_source_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Process a single source file and extract metadata.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Dictionary with file data, or None if file should be skipped
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Determine file type
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.dml':
                # Check if this is DML 1.2 (which we skip)
                if self.is_dml_1_2(content):
                    logging.info(f"    ⏭️  Skipping DML 1.2 file: {Path(file_path).name}")
                    return None
                
                file_type = 'dml'
                metadata = self.extract_dml_metadata(content, file_path)
            
            elif file_ext == '.py':
                file_type = 'python'
                metadata = self.extract_python_metadata(content, file_path)
            
            else:
                logging.warning(f"    ⚠️  Unknown file type: {file_ext}")
                return None
            
            # Determine source ID
            source_id = self.determine_source_id(file_type)
            
            return {
                'file_path': file_path,
                'content': content,
                'file_type': file_type,
                'source_id': source_id,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"    ❌ Error processing {file_path}: {e}")
            return None
    
    def smart_chunk_source(self, code: str, source_type: str = "python", 
                          max_chunk_size: int = 512, chunk_overlap: int = 0,
                          chunk_expansion: bool = False, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Chunk source code using AST-aware chunking with astchunk.
        
        This function uses the astchunk library to intelligently chunk source code
        while preserving syntactic structure (functions, classes, methods, etc.).
        
        Args:
            code: Source code to chunk
            source_type: Programming language type ("python" or "dml")
            max_chunk_size: Maximum non-whitespace characters per chunk (default: 512)
            chunk_overlap: Number of AST nodes to overlap between chunks (default: 0)
            chunk_expansion: Whether to add metadata headers to chunks (default: False)
            file_path: Optional file path for metadata
            
        Returns:
            List of dictionaries with 'content' and 'metadata' keys
            
        Example:
            >>> chunks = service.smart_chunk_source(python_code, source_type="python", max_chunk_size=512)
            >>> for chunk in chunks:
            ...     print(f"Chunk: {len(chunk['content'])} chars")
            ...     print(f"Lines: {chunk['metadata']['start_line']}-{chunk['metadata']['end_line']}")
        """
        try:
            from astchunk import ASTChunkBuilder
            
            # Validate source type
            supported_types = ["python", "dml"]
            if source_type not in supported_types:
                logging.warning(f"⚠️  Unsupported source type '{source_type}', falling back to simple chunking")
                return self._simple_chunk(code, max_chunk_size, 0)
            
            # Initialize AST chunk builder
            builder = ASTChunkBuilder(
                max_chunk_size=max_chunk_size,
                language=source_type,
                metadata_template="default"
            )
            
            # Prepare metadata
            repo_level_metadata = {}
            if file_path:
                repo_level_metadata["file_path"] = file_path
            
            # Generate chunks
            chunks = builder.chunkify(
                code=code,
                chunk_overlap=chunk_overlap,
                chunk_expansion=chunk_expansion,
                repo_level_metadata=repo_level_metadata
            )
            
            return chunks
            
        except ImportError as e:
            logging.warning(f"⚠️  astchunk not available ({e}), falling back to simple chunking")
            return self._simple_chunk(code, max_chunk_size, 0)
        except Exception as e:
            logging.warning(f"⚠️  Error in AST chunking ({e}), falling back to simple chunking")
            return self._simple_chunk(code, max_chunk_size, 0)
    
    def chunk_source_code(self, content: str, source_type: str, file_path: str, 
                         max_chunk_size: int = 2000, chunk_overlap: int = 0) -> List[Dict[str, Any]]:
        """
        Chunk source code using AST-aware chunking.
        
        Args:
            content: Source code content
            source_type: 'dml' or 'python'
            file_path: Path to the file
            max_chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        try:
            # Use internal smart_chunk_source method
            chunks = self.smart_chunk_source(
                code=content,
                source_type=source_type,
                max_chunk_size=max_chunk_size,
                chunk_overlap=chunk_overlap,
                file_path=file_path
            )
            
            logging.info(f"      ✓ Created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logging.error(f"      ❌ Error chunking source code: {e}")
            # Fallback to simple chunking
            return self._simple_chunk(content, max_chunk_size, chunk_overlap)
    
    def _simple_chunk(self, content: str, max_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Simple fallback chunking by lines."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            if current_size + line_size > max_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': '\n'.join(current_chunk),
                    'metadata': {'chunk_type': 'simple', 'line_count': len(current_chunk)}
                })
                # Start new chunk with overlap
                overlap_lines = max(0, len(current_chunk) - overlap)
                current_chunk = current_chunk[overlap_lines:]
                current_size = sum(len(l) + 1 for l in current_chunk)
            
            current_chunk.append(line)
            current_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': '\n'.join(current_chunk),
                'metadata': {'chunk_type': 'simple', 'line_count': len(current_chunk)}
            })
        
        return chunks
    
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
    
    def ingest_single_file(self, file_path: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Ingest a single source file into the RAG system.
        
        Workflow:
        1. Check if file should be skipped (DML 1.2, test filtering)
        2. Process file and extract metadata
        3. Generate file summary (if USE_CODE_SUMMARIZATION enabled)
        4. Check if already exists (unless force_reprocess)
        5. Chunk source code using AST-aware chunking
        6. Generate chunk summaries (if USE_CODE_SUMMARIZATION enabled)
        7. Generate embeddings and store in database
        
        Args:
            file_path: Path to source file
            force_reprocess: If True, remove existing data and re-ingest
            
        Returns:
            Dictionary with ingestion results
        """

        start_time = datetime.now()
        if self.should_skip_file(file_path):
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'skipped': True,
                'reason': 'File matches skip patterns',
                'processing_time': processing_time
            }
        
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            # Check if code summarization is enabled
            use_summarization = os.getenv("USE_CODE_SUMMARIZATION", "true").lower() == "true"
            
            # Process source file
            logging.info(f"📄 Processing source file: {Path(file_path).name}")
            file_data = self.process_source_file(file_path)
            
            if not file_data:
                return {
                    'success': False,
                    'skipped': True,
                    'reason': 'File skipped (DML 1.2 or unsupported type)'
                }
            
            content = file_data['content']
            metadata = file_data['metadata']
            source_type = metadata['language']
            source_id = file_data['source_id']
            
            # ========== STEP 1: Generate File Summary ==========
            file_summary = None
            if use_summarization:
                try:
                    logging.info("   📝 Step 1: Generating file summary...")
                    from ..code_summarizer import generate_file_summary
                    file_summary = generate_file_summary(content, metadata)
                    logging.info(f"      ✓ Summary: {file_summary[:80]}...")
                except Exception as e:
                    logging.warning(f"      ⚠️ Failed to generate file summary: {e}")
                    file_summary = None
            else:
                logging.info("   📝 Step 1: Skipped (summarization disabled)")
            
            # Calculate file hash and stats
            content_hash = self._calculate_file_hash(file_path)
            stats = self._get_file_stats(file_path)
            
            # Check if file already exists
            if not force_reprocess:
                existing = self.backend.check_file_exists(file_path, content_hash)
                if existing:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    return {
                        'success': True,
                        'skipped': True,
                        'file_id': existing['id'],
                        'chunks_created': existing.get('chunk_count', 0),
                        'word_count': existing.get('word_count', 0),
                        'reason': 'File unchanged',
                        'processing_time': processing_time
                    }
            else:
                # Force reprocess: remove existing data
                logging.info("   🔄 Force reprocess: removing existing data...")
                self.backend.remove_file_data(file_path)
            
            # Get git info if available
            git_info = None
            if self.git_service:
                git_info = self.git_service.detect_repository(Path(file_path))
            
            # Store file record
            logging.info("   💾 Storing file record...")
            if git_info:
                # Use temporal versioning
                repo = self.backend.get_repository(git_info.repo_url)
                if not repo:
                    repo_name = git_info.repo_url.split('/')[-1].replace('.git', '')
                    repo_id = self.backend.store_repository(git_info.repo_url, repo_name)
                else:
                    repo_id = repo['id']
                
                abs_file_path = Path(file_path).resolve()
                relative_path = git_info.get_relative_path(abs_file_path)
                
                file_version = {
                    'repo_id': repo_id,
                    'commit_sha': git_info.commit_sha,
                    'file_path': relative_path,
                    'content_hash': content_hash,
                    'file_size': stats['size'],
                    'word_count': 0,
                    'chunk_count': 0,
                    'content_type': f'code_{source_type}',
                    'valid_from': git_info.commit_timestamp,
                    'valid_until': None,
                    'ingested_at': datetime.now()
                }
                file_id = self.backend.store_file_version(file_version)
            else:
                # Legacy method for files outside git repos
                file_id = self.backend.store_file_record(
                    file_path=file_path,
                    content_hash=content_hash,
                    file_size=stats['size'],
                    content_type=f'code_{source_type}'
                )
            
            # Chunk source code
            logging.info(f"   📦 Step 2: Chunking {source_type.upper()} source code...")
            chunk_dicts = self.chunk_source_code(content, source_type, file_path)
            
            if not chunk_dicts:
                return {
                    'success': False,
                    'error': 'No chunks generated'
                }
            
            # ========== STEP 3: Generate Chunk Summaries ==========
            chunk_summaries = [None] * len(chunk_dicts)
            if use_summarization and file_summary and len(chunk_dicts) > 0:
                try:
                    logging.info(f"   📝 Step 3: Generating {len(chunk_dicts)} chunk summaries...")
                    from ..code_summarizer import generate_chunk_summary
                    for i, chunk_dict in enumerate(chunk_dicts):
                        chunk_meta = metadata.copy()
                        chunk_meta['chunk_type'] = chunk_dict.get("metadata", {}).get("chunk_type", "unknown")
                        chunk_summaries[i] = generate_chunk_summary(
                            chunk_dict["content"], 
                            file_summary, 
                            chunk_meta
                        )
                    logging.info(f"      ✓ Generated {len(chunk_dicts)} chunk summaries")
                except Exception as e:
                    logging.warning(f"      ⚠️ Failed to generate chunk summaries: {e}")
                    chunk_summaries = [None] * len(chunk_dicts)
            else:
                logging.info(f"   📝 Step 3: Skipped (no file summary or summarization disabled)")
            
            # Prepare chunk contents for embedding
            logging.info(f"   🔢 Step 4: Preparing {len(chunk_dicts)} chunks for embedding...")
            embedding_contents = []
            chunk_data_list = []
            
            for i, chunk_dict in enumerate(chunk_dicts):
                # Prepare content for embedding (with summaries if available)
                chunk_content = chunk_dict['content']
                if use_summarization and file_summary:
                    embedding_content = f"File: {file_summary}\n\n"
                    if chunk_summaries[i]:
                        embedding_content += f"Chunk: {chunk_summaries[i]}\n\n"
                    embedding_content += chunk_content
                else:
                    embedding_content = chunk_content
                
                embedding_contents.append(embedding_content)
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_index': i,
                    'source_id': source_id,
                    'source_type': source_type,
                    'content_type': f'code_{source_type}',  # Set content_type for ChromaDB
                    'chunking_method': 'ast_aware',
                    'has_summarization': use_summarization,
                    'char_count': len(chunk_content),
                    'content': chunk_content,  # Store original content
                    'heading_hierarchy': [],  # Default for source code
                    'has_code': True,  # Source code always has code
                    'language_hints': [source_type]  # Programming language
                })
                
                # Add summarization metadata if available
                if use_summarization and file_summary:
                    chunk_metadata['file_summary'] = file_summary
                    if chunk_summaries[i]:
                        chunk_metadata['chunk_summary'] = chunk_summaries[i]
                
                if chunk_dict.get('metadata'):
                    chunk_metadata.update(chunk_dict['metadata'])
                
                chunk_data_list.append({
                    'content': chunk_content,
                    'metadata': chunk_metadata,
                    'summary': chunk_summaries[i] if use_summarization and chunk_summaries[i] else None
                })
            
            logging.info(f"      ✓ Prepared {len(chunk_data_list)} chunks with {'summaries' if use_summarization else 'raw content'}")
            
            # ========== STEP 4.5: Generate Embeddings ==========
            logging.info(f"   🧠 Step 4.5: Generating embeddings for {len(embedding_contents)} chunks...")
            try:
                from utils import create_embeddings_batch
                embeddings = create_embeddings_batch(embedding_contents)
                logging.info(f"      ✓ Generated {len(embeddings)} embeddings (dim: {len(embeddings[0]) if embeddings else 0})")
            except Exception as e:
                logging.error(f"      ❌ Failed to generate embeddings: {e}")
                # Fall back to empty embeddings
                embeddings = [None] * len(embedding_contents)
            
            # ========== STEP 5: Create ChunkWithEmbedding objects ==========
            logging.info(f"   📦 Step 5: Creating chunk objects with embeddings...")
            chunks_to_store = []
            for i, chunk_data in enumerate(chunk_data_list):
                chunk_obj = ChunkWithEmbedding(
                    content=chunk_data['content'],
                    metadata=chunk_data['metadata'],
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    summary=chunk_data['summary']
                )
                chunks_to_store.append(chunk_obj)
            
            logging.info(f"      ✓ Created {len(chunks_to_store)} chunk objects")
            
            # Store chunks (embeddings already generated)
            logging.info(f"   💾 Step 6: Storing chunks in database...")
            result = self.backend.store_chunks(file_id, chunks_to_store, file_path)
            logging.info(f"      ✓ Stored chunks successfully: {result.get('chunks_stored', 0)} chunks")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logging.info(f"   ✅ File completed successfully!")
            
            return {
                'success': True,
                'file_id': file_id,
                'chunks_created': result.get('chunks_stored', len(chunks_to_store)),
                'word_count': sum(len(c.content.split()) for c in chunks_to_store),
                'processing_time': processing_time,
                'source_type': source_type,
                'source_id': source_id,
                'has_summarization': use_summarization,
                'file_summary': file_summary if use_summarization else None,
                'embeddings_generated': sum(1 for c in chunks_to_store if c.embedding is not None)
            }
            
        except Exception as e:
            logging.error(f"   ❌ Error ingesting source file: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
