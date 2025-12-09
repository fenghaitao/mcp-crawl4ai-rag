"""
Bulk Ingest Service - Process multiple documentation files.

This service handles bulk ingestion of multiple documentation files with:
- File discovery and pattern matching
- Sequential or parallel processing
- Progress tracking
- Validation and error reporting
- Integration with DocumentIngestService
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import psutil
import time
import threading


@dataclass
class BulkProgress:
    """Progress tracking for batch operations."""
    total_files: int
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    files_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    peak_memory_mb: float = 0.0
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        return (self.processed / self.total_files * 100) if self.total_files > 0 else 0.0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def update_metrics(self):
        """Update performance metrics."""
        if self.elapsed_time > 0:
            self.files_per_second = self.processed / self.elapsed_time
        
        # Get current memory usage
        process = psutil.Process()
        self.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        
        # Track peak memory usage
        if self.memory_usage_mb > self.peak_memory_mb:
            self.peak_memory_mb = self.memory_usage_mb


class BulkIngestService:
    """Service for bulk document ingestion with optional parallel processing."""
    
    def __init__(self, backend, git_service, ingest_service):
        """
        Initialize bulk ingest service.
        
        Args:
            backend: DatabaseBackend instance
            git_service: GitService instance
            ingest_service: DocumentIngestService instance
        """
        self.backend = backend
        self.git_service = git_service
        self.ingest_service = ingest_service
        
        # Import configuration
        from ..config.batch_config import config
        self.config = config
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Thread lock for progress updates
        self._progress_lock = threading.Lock()
    
    def discover_files(self, directory: Path, pattern: str = "*.md", 
                      recursive: bool = True) -> List[Path]:
        """
        Discover files matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (e.g., *.md, *.html) or comma-separated patterns
            recursive: Whether to search subdirectories
            
        Returns:
            Sorted list of file paths
            
        Requirements: 2.1, 2.2, 2.3
        """
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        discovered_files = set()
        
        # Support multiple patterns separated by comma
        patterns = [p.strip() for p in pattern.split(',')]
        
        for pat in patterns:
            if recursive:
                # Use rglob for recursive search
                matched_files = directory.rglob(pat)
            else:
                # Use glob for non-recursive search
                matched_files = directory.glob(pat)
            
            # Add only files (not directories) to the set
            for file_path in matched_files:
                if file_path.is_file():
                    discovered_files.add(file_path)
        
        # Return sorted list of file paths
        return sorted(discovered_files)
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate file before processing.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dict with 'valid', 'issues', 'warnings' keys
            
        Requirements: 12.1, 12.2, 12.3, 12.4
        """
        issues = []
        warnings = []
        
        # Check file exists and is readable (Requirement 12.1)
        if not file_path.exists():
            issues.append(f"File does not exist: {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        if not file_path.is_file():
            issues.append(f"Path is not a file: {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        try:
            # Test if file is readable
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Try to read one character
        except PermissionError:
            issues.append(f"File is not readable (permission denied): {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        except UnicodeDecodeError:
            # Binary files or non-UTF8 files
            warnings.append(f"File may not be UTF-8 encoded: {file_path}")
        except Exception as e:
            issues.append(f"Cannot read file: {file_path} - {str(e)}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Check file size is within acceptable limits (Requirement 12.2)
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            issues.append(f"File is empty: {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        if file_size > self.config.max_file_size:
            issues.append(f"File exceeds maximum size ({self.config.max_file_size / 1024 / 1024:.0f}MB): {file_path} ({file_size / 1024 / 1024:.2f}MB)")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Warn if file is large
        if file_size > self.config.warn_file_size:
            warnings.append(f"File is large ({file_size / 1024 / 1024:.2f}MB): {file_path}")
        
        # Check file format is supported (Requirement 12.3)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.config.supported_extensions:
            issues.append(f"Unsupported file format '{file_extension}': {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # File is valid (Requirement 12.4)
        return {'valid': True, 'issues': issues, 'warnings': warnings}
    
    def _get_completed_files_from_database(self, directory: Path) -> set:
        """
        Get already-ingested files from database.
        
        Args:
            directory: Directory being processed
            
        Returns:
            Set of completed file paths (relative to git root)
            
        Requirements: 4.1, 4.2, 4.4
        """
        completed_files = set()
        
        try:
            # Detect git repository
            git_info = self.git_service.detect_repository(directory)
            
            if git_info:
                # Get repository from database
                repo = self.backend.get_repository(git_info.repo_url)
                
                if repo:
                    # Query all current files in this repository
                    files, _ = self.backend.list_files(
                        repo_id=repo['id'],
                        current_only=True,
                        limit=10000  # Large limit to get all files
                    )
                    
                    # Extract file paths
                    for f in files:
                        completed_files.add(f['file_path'])
                    
                    self.logger.info(f"Found {len(completed_files)} files already in database")
            else:
                self.logger.warning("Not a git repository - cannot check database for existing files")
        
        except Exception as e:
            self.logger.warning(f"Failed to query database for completed files: {e}")
        
        return completed_files
    
    def _process_files_sequential(self, files: List[Path], progress: BulkProgress, 
                                  directory: Path, completed_files: set, 
                                  force: bool = False) -> None:
        """
        Process files sequentially in chunks for better memory management.
        
        Args:
            files: List of files to process
            progress: Progress tracking object
            directory: Base directory for relative path calculation
            completed_files: Set of already completed files (relative paths)
            force: Force reprocess existing files
        """
        from ..utils.retry import retry, with_retry_logging
        
        chunk_size = self.config.chunk_processing_size
        
        # Get git info for relative path calculation
        git_info = self.git_service.detect_repository(directory)
        
        # Process files in chunks
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            
            # Check memory usage before processing chunk
            progress.update_metrics()
            if progress.memory_usage_mb > self.config.memory_threshold_mb:
                self.logger.warning(
                    f"High memory usage: {progress.memory_usage_mb:.1f}MB "
                    f"(threshold: {self.config.memory_threshold_mb}MB)"
                )
            
            self.logger.info(
                f"Processing chunk {i//chunk_size + 1}/{(len(files) + chunk_size - 1)//chunk_size} "
                f"({len(chunk)} files)"
            )
            
            for file_path in chunk:
                file_path_str = str(file_path.absolute())
                
                # Calculate relative path for database comparison
                if git_info:
                    relative_path = git_info.get_relative_path(file_path.resolve())
                else:
                    relative_path = str(file_path)
                
                # Skip if already completed (unless force mode)
                if not force and relative_path in completed_files:
                    progress.skipped += 1
                    progress.processed += 1
                    self.logger.debug(f"Skipping already-ingested file: {relative_path}")
                    continue
                
                # Validate file before processing
                validation = self.validate_file(file_path)
                if not validation['valid']:
                    progress.processed += 1
                    progress.failed += 1
                    progress.errors.append({
                        'file': file_path_str,
                        'type': 'validation',
                        'issues': validation['issues']
                    })
                    continue
                
                # Process with retry logic
                self._process_single_file_with_retry(
                    file_path_str, force, progress
                )
                
                # Update metrics and show progress for every file with visual emphasis
                progress.update_metrics()
                print(f"\n{'='*60}")
                print(f"🔄 PROGRESS: {progress.progress_percent:.1f}% ({progress.processed}/{progress.total_files})")
                print(f"📄 Processing: {file_path.name}")
                print(f"⏱️  Rate: {progress.files_per_second:.1f} files/sec")
                print(f"{'='*60}\n")
                
                # Log detailed metrics periodically
                if progress.processed % self.config.progress_save_interval == 0:
                    self.logger.info(
                        f"Progress: {progress.progress_percent:.1f}% "
                        f"({progress.processed}/{progress.total_files}), "
                        f"Rate: {progress.files_per_second:.1f} files/sec, "
                        f"Memory: {progress.memory_usage_mb:.1f}MB"
                    )
    
    def _process_files_parallel(self, files: List[Path], progress: BulkProgress,
                               directory: Path, completed_files: set,
                               force: bool = False, max_workers: int = 4) -> None:
        """
        Process files in parallel using ThreadPoolExecutor.
        
        Args:
            files: List of files to process
            progress: Progress tracking object
            directory: Base directory for relative path calculation
            completed_files: Set of already completed files (relative paths)
            force: Force reprocess existing files
            max_workers: Number of parallel workers
        """
        # Get git info for relative path calculation
        git_info = self.git_service.detect_repository(directory)
        
        # Filter files to process
        files_to_process = []
        for file_path in files:
            # Calculate relative path for database comparison
            if git_info:
                relative_path = git_info.get_relative_path(file_path.resolve())
            else:
                relative_path = str(file_path)
            
            # Skip if already completed (unless force mode)
            if not force and relative_path in completed_files:
                with self._progress_lock:
                    progress.skipped += 1
                    progress.processed += 1
                self.logger.debug(f"Skipping already-ingested file: {relative_path}")
                continue
            
            # Validate file before processing
            validation = self.validate_file(file_path)
            if not validation['valid']:
                with self._progress_lock:
                    progress.processed += 1
                    progress.failed += 1
                    progress.errors.append({
                        'file': str(file_path.absolute()),
                        'type': 'validation',
                        'issues': validation['issues']
                    })
                continue
            
            files_to_process.append(file_path)
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file_with_retry, str(f.absolute()), force, progress): f
                for f in files_to_process
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    future.result()  # This will raise if the task failed
                except Exception as e:
                    self.logger.error(f"Unexpected error processing {file_path}: {e}")
                
                # Update metrics and show progress for every file with visual emphasis
                with self._progress_lock:
                    progress.update_metrics()
                    print(f"\n{'='*60}")
                    print(f"✅ PROGRESS: {progress.progress_percent:.1f}% ({progress.processed}/{progress.total_files})")
                    print(f"📄 Completed: {file_path.name}")
                    print(f"⏱️  Rate: {progress.files_per_second:.1f} files/sec")
                    print(f"{'='*60}\n")
                    
                    # Log detailed metrics periodically
                    if progress.processed % self.config.progress_save_interval == 0:
                        self.logger.info(
                            f"Progress: {progress.progress_percent:.1f}% "
                            f"({progress.processed}/{progress.total_files}), "
                            f"Rate: {progress.files_per_second:.1f} files/sec, "
                            f"Memory: {progress.memory_usage_mb:.1f}MB"
                        )
    
    def _process_single_file_with_retry(self, file_path: str, force: bool, 
                                      progress: BulkProgress) -> None:
        """
        Process a single file with retry logic.
        
        Args:
            file_path: File path to process
            force: Force reprocess existing files
            progress: Progress tracking object
        """
        from ..utils.retry import retry, with_retry_logging
        
        # Create retry decorator with configuration
        @retry(
            max_attempts=self.config.max_retry_attempts,
            backoff_factor=self.config.retry_backoff_factor,
            exceptions=(Exception,),
            on_retry=with_retry_logging
        )
        def process_with_retry():
            return self.ingest_service.ingest_document(
                file_path, force_reprocess=force
            )
        
        try:
            result = process_with_retry()
            
            # Thread-safe progress updates
            with self._progress_lock:
                progress.processed += 1
                
                if result['success']:
                    if result.get('skipped'):
                        progress.skipped += 1
                    else:
                        progress.succeeded += 1
                else:
                    # Record processing error
                    progress.failed += 1
                    progress.errors.append({
                        'file': file_path,
                        'type': 'processing',
                        'error': result.get('error', 'Unknown error')
                    })
                
        except Exception as e:
            # All retries exhausted
            with self._progress_lock:
                progress.processed += 1
                progress.failed += 1
                progress.errors.append({
                    'file': file_path,
                    'type': 'exception_after_retries',
                    'error': f"Failed after {self.config.max_retry_attempts} attempts: {str(e)}"
                })
            self.logger.error(f"Failed to process {file_path} after retries: {e}")
    

    
    def ingest_bulk(self, directory: Path, pattern: str = "*.md",
                   recursive: bool = True, force: bool = False,
                   dry_run: bool = False, parallel: bool = False,
                   max_workers: int = 4) -> BulkProgress:
        """
        Ingest multiple files with progress tracking.
        
        Args:
            directory: Directory containing files
            pattern: File pattern to match
            recursive: Search subdirectories
            force: Force reprocess existing files
            dry_run: Validate without processing
            parallel: Enable parallel processing (default: False for sequential)
            max_workers: Number of parallel workers (default: 4)
            
        Returns:
            BulkProgress with results
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5,
                     4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5,
                     6.1, 6.2, 6.3, 6.4, 6.5
        """
        # Discover files matching pattern (Requirements 2.1, 2.2, 2.3)
        files = self.discover_files(directory, pattern, recursive)
        
        # Initialize progress tracking
        progress = BulkProgress(total_files=len(files))
        
        # Get already-completed files from database (Requirement 4.1, 4.4)
        # This replaces the JSON progress file approach
        completed_files = set()
        if not force:
            completed_files = self._get_completed_files_from_database(directory)
        
        # Dry-run mode: validate all files without processing (Requirement 12.5)
        if dry_run:
            for file_path in files:
                validation = self.validate_file(file_path)
                progress.processed += 1
                
                if not validation['valid']:
                    progress.failed += 1
                    progress.errors.append({
                        'file': str(file_path),
                        'type': 'validation',
                        'issues': validation['issues']
                    })
                else:
                    progress.succeeded += 1
                    
                # Display warnings if any
                if validation['warnings']:
                    for warning in validation['warnings']:
                        progress.errors.append({
                            'file': str(file_path),
                            'type': 'warning',
                            'message': warning
                        })
            
            # Generate error report in dry-run mode too if errors occurred
            if progress.errors:
                error_report_path = directory / "bulk_ingest_errors.json"
                self._generate_error_report(progress.errors, error_report_path)
            
            return progress
        
        # Choose processing mode
        if parallel:
            self.logger.info(f"Using parallel processing with {max_workers} workers")
            self._process_files_parallel(files, progress, directory, completed_files, force, max_workers)
        else:
            self.logger.info("Using sequential processing")
            self._process_files_sequential(files, progress, directory, completed_files, force)
        
        # Generate error report if failures occurred (Requirement 6.2)
        if progress.errors:
            error_report_path = directory / "bulk_ingest_errors.json"
            self._generate_error_report(progress.errors, error_report_path)
        
        # Generate performance report
        self._generate_performance_report(progress, directory)
        
        # Final metrics update
        progress.update_metrics()
        
        return progress
    
    def _generate_error_report(self, errors: List[Dict[str, Any]], output_path: Path):
        """
        Generate error report file.
        
        Args:
            errors: List of error dictionaries
            output_path: Path to write error report
            
        Requirements: 6.1, 6.2, 6.3, 6.4
        """
        import json
        from datetime import datetime
        
        # Group errors by type for summary
        error_types = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Create error report structure (Requirement 6.3)
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': len(errors),
            'error_summary': error_types,
            'errors': errors
        }
        
        # Write error report to file (Requirement 6.2)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
        except IOError as e:
            # If we can't write the error report, at least don't crash
            pass
    
    def _generate_performance_report(self, progress: BulkProgress, output_dir: Path):
        """
        Generate performance report file.
        
        Args:
            progress: BatchProgress with performance metrics
            output_dir: Directory to write performance report
        """
        import json
        from datetime import datetime
        
        # Create performance report structure
        report = {
            'timestamp': datetime.now().isoformat(),
            'processing_summary': {
                'total_files': progress.total_files,
                'processed': progress.processed,
                'succeeded': progress.succeeded,
                'failed': progress.failed,
                'skipped': progress.skipped,
                'success_rate': (progress.succeeded / progress.processed * 100) if progress.processed > 0 else 0
            },
            'performance_metrics': {
                'elapsed_time_seconds': progress.elapsed_time,
                'files_per_second': progress.files_per_second,
                'memory_usage_mb': progress.memory_usage_mb,
                'peak_memory_mb': progress.peak_memory_mb
            },
            'configuration': {
                'max_file_size_mb': self.config.max_file_size / 1024 / 1024,
                'chunk_processing_size': self.config.chunk_processing_size,
                'max_retry_attempts': self.config.max_retry_attempts,
                'memory_threshold_mb': self.config.memory_threshold_mb
            }
        }
        
        # Write performance report to file
        output_path = output_dir / "bulk_ingest_performance.json"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Performance report written to {output_path}")
        except IOError as e:
            self.logger.warning(f"Failed to write performance report: {e}")
    
    def get_processing_metrics(self, progress: BulkProgress) -> Dict[str, Any]:
        """
        Get current processing metrics.
        
        Args:
            progress: Current batch progress
            
        Returns:
            Dict with current metrics
        """
        progress.update_metrics()
        
        return {
            'progress_percent': progress.progress_percent,
            'files_per_second': progress.files_per_second,
            'memory_usage_mb': progress.memory_usage_mb,
            'peak_memory_mb': progress.peak_memory_mb,
            'elapsed_time': progress.elapsed_time,
            'estimated_time_remaining': (
                (progress.total_files - progress.processed) / progress.files_per_second 
                if progress.files_per_second > 0 else None
            )
        }
