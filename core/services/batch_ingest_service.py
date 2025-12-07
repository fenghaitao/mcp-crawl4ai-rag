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
from typing import List, Dict, Any, Optional


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
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        return (self.processed / self.total_files * 100) if self.total_files > 0 else 0.0


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
        # 0 < size < 50MB
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
        file_size = file_path.stat().st_size
        
        if file_size == 0:
            issues.append(f"File is empty: {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        if file_size > MAX_FILE_SIZE:
            issues.append(f"File exceeds maximum size (50MB): {file_path} ({file_size / 1024 / 1024:.2f}MB)")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # Warn if file is large (> 10MB)
        if file_size > 10 * 1024 * 1024:
            warnings.append(f"File is large ({file_size / 1024 / 1024:.2f}MB): {file_path}")
        
        # Check file format is supported (Requirement 12.3)
        SUPPORTED_EXTENSIONS = {'.md', '.html', '.htm', '.rst', '.txt', '.dml', '.py'}
        file_extension = file_path.suffix.lower()
        
        if file_extension not in SUPPORTED_EXTENSIONS:
            issues.append(f"Unsupported file format '{file_extension}': {file_path}")
            return {'valid': False, 'issues': issues, 'warnings': warnings}
        
        # File is valid (Requirement 12.4)
        return {'valid': True, 'issues': issues, 'warnings': warnings}
    
    def _load_progress(self, progress_file: Path) -> set:
        """
        Load completed files from progress file.
        
        Args:
            progress_file: Path to progress tracking file
            
        Returns:
            Set of completed file paths
            
        Requirements: 4.1, 4.2, 4.4
        """
        import json
        
        if not progress_file.exists():
            return set()
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Return set of completed file paths
                return set(data.get('completed_files', []))
        except (json.JSONDecodeError, IOError) as e:
            # If progress file is corrupted, start fresh
            return set()
    
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
        
        # Process files sequentially (Requirement 2.4)
        for file_path in files:
            file_path_str = str(file_path.absolute())
            
            # Skip if already completed (Requirement 4.4)
            if file_path_str in completed_files:
                progress.skipped += 1
                progress.processed += 1
                continue
            
            # Validate file before processing
            validation = self.validate_file(file_path)
            
            if not validation['valid']:
                # Record validation error and continue (Requirement 3.4, 6.1)
                progress.processed += 1
                progress.failed += 1
                progress.errors.append({
                    'file': file_path_str,
                    'type': 'validation',
                    'issues': validation['issues']
                })
                continue
            
            # Process file with DocumentIngestService
            try:
                result = self.ingest_service.ingest_document(
                    file_path_str,
                    force_reprocess=force
                )
                
                progress.processed += 1
                
                if result['success']:
                    if result.get('skipped'):
                        progress.skipped += 1
                    else:
                        progress.succeeded += 1
                    
                    # Save progress after successful processing (Requirement 4.2)
                    self._save_progress(progress_file, file_path_str)
                else:
                    # Record processing error and continue (Requirement 3.4, 6.1)
                    progress.failed += 1
                    progress.errors.append({
                        'file': file_path_str,
                        'type': 'processing',
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                # Handle exceptions gracefully (Requirement 13.4, 6.1)
                progress.processed += 1
                progress.failed += 1
                progress.errors.append({
                    'file': file_path_str,
                    'type': 'exception',
                    'error': str(e)
                })
        
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
