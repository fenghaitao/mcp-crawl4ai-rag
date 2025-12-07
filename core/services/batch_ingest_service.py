"""
Batch Ingest Service - Batch processing for document ingestion.

This service handles batch ingestion of multiple documentation files with:
- File discovery and pattern matching
- Progress tracking and resume capability
- Validation and error reporting
- Integration with DocumentIngestService
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import logging
import psutil
import time


@dataclass
class BatchProgress:
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


class BatchIngestService:
    """Service for batch document ingestion."""
    
    def __init__(self, backend, git_service, ingest_service):
        """
        Initialize batch ingest service.
        
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
    
    def _load_progress(self, progress_file: Path) -> set:
        """
        Load completed files from progress file with corruption recovery.
        
        Args:
            progress_file: Path to progress tracking file
            
        Returns:
            Set of completed file paths
            
        Requirements: 4.1, 4.2, 4.4
        """
        import json
        import shutil
        import logging
        
        logger = logging.getLogger(__name__)
        
        if not progress_file.exists():
            return set()
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                completed_files = data.get('completed_files', [])
                
                # Validate data structure
                if not isinstance(completed_files, list):
                    raise ValueError("Invalid progress file format: completed_files should be a list")
                
                # Filter out invalid entries
                valid_files = set()
                for file_path in completed_files:
                    if isinstance(file_path, str) and file_path.strip():
                        valid_files.add(file_path.strip())
                    else:
                        logger.warning(f"Invalid file path in progress file: {file_path}")
                
                logger.info(f"Loaded {len(valid_files)} completed files from progress")
                return valid_files
                
        except (json.JSONDecodeError, IOError, ValueError) as e:
            # Create backup and attempt recovery
            backup_file = progress_file.with_suffix('.backup')
            try:
                shutil.copy(progress_file, backup_file)
                logger.warning(
                    f"Progress file corrupted ({e}), backup saved to {backup_file}. "
                    f"Starting fresh."
                )
            except Exception as backup_error:
                logger.error(f"Failed to create backup: {backup_error}")
            
            # Attempt simple text recovery (look for file paths)
            recovered_files = self._attempt_progress_recovery(progress_file)
            if recovered_files:
                logger.info(f"Recovered {len(recovered_files)} files from corrupted progress")
                return recovered_files
            
            return set()
    
    def _attempt_progress_recovery(self, progress_file: Path) -> set:
        """
        Attempt to recover file paths from corrupted progress file.
        
        Args:
            progress_file: Path to corrupted progress file
            
        Returns:
            Set of recovered file paths
        """
        import re
        import logging
        
        logger = logging.getLogger(__name__)
        recovered_files = set()
        
        try:
            with open(progress_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Look for file path patterns (common extensions)
                path_pattern = r'["\']([^"\']*\.(?:md|html?|rst|txt|dml|py|json|ya?ml))["\']'
                matches = re.findall(path_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    if Path(match).is_absolute() or '/' in match or '\\' in match:
                        recovered_files.add(match)
                        
                logger.info(f"Recovery attempt found {len(recovered_files)} potential file paths")
                
        except Exception as e:
            logger.error(f"Failed to recover from corrupted progress file: {e}")
        
        return recovered_files
    
    def _process_files_in_chunks(self, files: List[Path], progress: BatchProgress, 
                                progress_file: Path, completed_files: set, 
                                force: bool = False) -> None:
        """
        Process files in configurable chunks for better memory management.
        
        Args:
            files: List of files to process
            progress: Progress tracking object
            progress_file: Progress file for checkpointing
            completed_files: Set of already completed files
            force: Force reprocess existing files
        """
        from ..utils.retry import retry, with_retry_logging
        
        chunk_size = self.config.chunk_processing_size
        
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
                
                # Skip if already completed
                if file_path_str in completed_files:
                    progress.skipped += 1
                    progress.processed += 1
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
                success = self._process_single_file_with_retry(
                    file_path_str, force, progress
                )
                
                if success:
                    # Save progress after successful processing
                    self._save_progress(progress_file, file_path_str)
                
                # Update metrics periodically
                if progress.processed % self.config.progress_save_interval == 0:
                    progress.update_metrics()
                    self.logger.info(
                        f"Progress: {progress.progress_percent:.1f}% "
                        f"({progress.processed}/{progress.total_files}), "
                        f"Rate: {progress.files_per_second:.1f} files/sec, "
                        f"Memory: {progress.memory_usage_mb:.1f}MB"
                    )
    
    def _process_single_file_with_retry(self, file_path: str, force: bool, 
                                      progress: BatchProgress) -> bool:
        """
        Process a single file with retry logic.
        
        Args:
            file_path: File path to process
            force: Force reprocess existing files
            progress: Progress tracking object
            
        Returns:
            True if successful, False otherwise
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
            progress.processed += 1
            
            if result['success']:
                if result.get('skipped'):
                    progress.skipped += 1
                else:
                    progress.succeeded += 1
                return True
            else:
                # Record processing error
                progress.failed += 1
                progress.errors.append({
                    'file': file_path,
                    'type': 'processing',
                    'error': result.get('error', 'Unknown error')
                })
                return False
                
        except Exception as e:
            # All retries exhausted
            progress.processed += 1
            progress.failed += 1
            progress.errors.append({
                'file': file_path,
                'type': 'exception_after_retries',
                'error': f"Failed after {self.config.max_retry_attempts} attempts: {str(e)}"
            })
            self.logger.error(f"Failed to process {file_path} after retries: {e}")
            return False
    
    def _save_progress(self, progress_file: Path, file_path: str):
        """
        Save completed file to progress file.
        
        Args:
            progress_file: Path to progress tracking file
            file_path: Path of completed file to record
            
        Requirements: 4.1, 4.2, 4.3
        """
        import json
        from datetime import datetime
        
        # Load existing progress
        completed_files = list(self._load_progress(progress_file))
        
        # Add new file if not already present
        if file_path not in completed_files:
            completed_files.append(file_path)
        
        # Save updated progress
        progress_data = {
            'version': '1.0',
            'completed_files': completed_files,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
        except IOError as e:
            # Log error but don't fail the batch operation
            pass
    
    def ingest_batch(self, directory: Path, pattern: str = "*.md",
                    recursive: bool = True, force: bool = False,
                    dry_run: bool = False, resume: bool = False) -> BatchProgress:
        """
        Ingest multiple files with progress tracking.
        
        Args:
            directory: Directory containing files
            pattern: File pattern to match
            recursive: Search subdirectories
            force: Force reprocess existing files
            dry_run: Validate without processing
            resume: Resume from previous progress
            
        Returns:
            BatchProgress with results
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5,
                     4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5,
                     6.1, 6.2, 6.3, 6.4, 6.5
        """
        # Discover files matching pattern (Requirements 2.1, 2.2, 2.3)
        files = self.discover_files(directory, pattern, recursive)
        
        # Initialize progress tracking
        progress = BatchProgress(total_files=len(files))
        
        # Set up progress file for resume capability (Requirement 4.1)
        progress_file = directory / ".batch_ingest_progress.json"
        completed_files = set()
        
        # Load progress if resuming (Requirement 4.4)
        if resume:
            completed_files = self._load_progress(progress_file)
        
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
                error_report_path = directory / "batch_ingest_errors.json"
                self._generate_error_report(progress.errors, error_report_path)
            
            return progress
        
        # Process files in chunks with improved memory management and retry logic
        self._process_files_in_chunks(files, progress, progress_file, completed_files, force)
        
        # Remove progress file when all files completed (Requirement 4.5)
        if progress.processed == progress.total_files and progress_file.exists():
            try:
                progress_file.unlink()
            except Exception:
                pass  # Ignore errors when removing progress file
        
        # Generate error report if failures occurred (Requirement 6.2)
        if progress.errors:
            error_report_path = directory / "batch_ingest_errors.json"
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
    
    def _generate_performance_report(self, progress: BatchProgress, output_dir: Path):
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
        output_path = output_dir / "batch_ingest_performance.json"
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Performance report written to {output_path}")
        except IOError as e:
            self.logger.warning(f"Failed to write performance report: {e}")
    
    def get_processing_metrics(self, progress: BatchProgress) -> Dict[str, Any]:
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
