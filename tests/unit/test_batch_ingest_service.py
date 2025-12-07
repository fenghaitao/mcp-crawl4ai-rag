"""
Unit tests for BatchIngestService.

Tests file discovery, validation, progress tracking, and error handling.
"""

import pytest
from pathlib import Path
from datetime import datetime
from core.services.batch_ingest_service import BatchIngestService, BatchProgress


class TestFileDiscovery:
    """Test file discovery functionality."""
    
    def test_discover_files_single_pattern(self, tmp_path):
        """Test discovering files with a single pattern."""
        # Create test files
        (tmp_path / "file1.md").write_text("# Test 1")
        (tmp_path / "file2.md").write_text("# Test 2")
        (tmp_path / "file3.txt").write_text("Not markdown")
        
        # Create service (backend and git_service can be None for this test)
        service = BatchIngestService(None, None, None)
        
        # Discover markdown files
        files = service.discover_files(tmp_path, "*.md", recursive=False)
        
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)
        assert files == sorted(files)  # Verify sorted
    
    def test_discover_files_multiple_patterns(self, tmp_path):
        """Test discovering files with multiple patterns."""
        # Create test files
        (tmp_path / "file1.md").write_text("# Test 1")
        (tmp_path / "file2.html").write_text("<html></html>")
        (tmp_path / "file3.rst").write_text("Test RST")
        (tmp_path / "file4.txt").write_text("Not included")
        
        service = BatchIngestService(None, None, None)
        
        # Discover with multiple patterns
        files = service.discover_files(tmp_path, "*.md,*.html,*.rst", recursive=False)
        
        assert len(files) == 3
        assert any(f.suffix == ".md" for f in files)
        assert any(f.suffix == ".html" for f in files)
        assert any(f.suffix == ".rst" for f in files)
        assert files == sorted(files)
    
    def test_discover_files_recursive(self, tmp_path):
        """Test recursive file discovery."""
        # Create nested directory structure
        (tmp_path / "file1.md").write_text("# Root")
        subdir1 = tmp_path / "subdir1"
        subdir1.mkdir()
        (subdir1 / "file2.md").write_text("# Subdir1")
        subdir2 = subdir1 / "subdir2"
        subdir2.mkdir()
        (subdir2 / "file3.md").write_text("# Subdir2")
        
        service = BatchIngestService(None, None, None)
        
        # Discover recursively
        files = service.discover_files(tmp_path, "*.md", recursive=True)
        
        assert len(files) == 3
        assert files == sorted(files)
    
    def test_discover_files_non_recursive(self, tmp_path):
        """Test non-recursive file discovery."""
        # Create nested directory structure
        (tmp_path / "file1.md").write_text("# Root")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.md").write_text("# Subdir")
        
        service = BatchIngestService(None, None, None)
        
        # Discover non-recursively
        files = service.discover_files(tmp_path, "*.md", recursive=False)
        
        assert len(files) == 1
        assert files[0].name == "file1.md"
    
    def test_discover_files_empty_directory(self, tmp_path):
        """Test discovering files in empty directory."""
        service = BatchIngestService(None, None, None)
        
        files = service.discover_files(tmp_path, "*.md", recursive=True)
        
        assert len(files) == 0
        assert files == []
    
    def test_discover_files_no_matches(self, tmp_path):
        """Test discovering files when no files match pattern."""
        (tmp_path / "file1.txt").write_text("Text file")
        (tmp_path / "file2.py").write_text("Python file")
        
        service = BatchIngestService(None, None, None)
        
        files = service.discover_files(tmp_path, "*.md", recursive=True)
        
        assert len(files) == 0
    
    def test_discover_files_invalid_directory(self):
        """Test discovering files with invalid directory."""
        service = BatchIngestService(None, None, None)
        
        with pytest.raises(ValueError, match="Directory does not exist"):
            service.discover_files(Path("/nonexistent/path"), "*.md")
    
    def test_discover_files_path_is_file(self, tmp_path):
        """Test discovering files when path is a file, not directory."""
        file_path = tmp_path / "file.md"
        file_path.write_text("# Test")
        
        service = BatchIngestService(None, None, None)
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            service.discover_files(file_path, "*.md")
    
    def test_discover_files_excludes_directories(self, tmp_path):
        """Test that directories matching pattern are excluded."""
        # Create a directory that matches the pattern
        (tmp_path / "test.md").mkdir()
        # Create actual files
        (tmp_path / "file1.md").write_text("# Test")
        
        service = BatchIngestService(None, None, None)
        
        files = service.discover_files(tmp_path, "*.md", recursive=False)
        
        # Should only find the file, not the directory
        assert len(files) == 1
        assert files[0].is_file()
        assert files[0].name == "file1.md"


class TestFileValidation:
    """Test file validation functionality."""
    
    def test_validate_file_valid_markdown(self, tmp_path):
        """Test validating a valid markdown file."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test Document\n\nSome content here.")
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
        assert len(result['warnings']) == 0
    
    def test_validate_file_valid_html(self, tmp_path):
        """Test validating a valid HTML file."""
        file_path = tmp_path / "test.html"
        file_path.write_text("<html><body>Test</body></html>")
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
    
    def test_validate_file_valid_rst(self, tmp_path):
        """Test validating a valid RST file."""
        file_path = tmp_path / "test.rst"
        file_path.write_text("Test Document\n=============\n\nContent here.")
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
    
    def test_validate_file_does_not_exist(self, tmp_path):
        """Test validating a non-existent file."""
        file_path = tmp_path / "nonexistent.md"
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is False
        assert len(result['issues']) == 1
        assert "does not exist" in result['issues'][0]
    
    def test_validate_file_is_directory(self, tmp_path):
        """Test validating a directory instead of file."""
        dir_path = tmp_path / "testdir"
        dir_path.mkdir()
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(dir_path)
        
        assert result['valid'] is False
        assert len(result['issues']) == 1
        assert "not a file" in result['issues'][0]
    
    def test_validate_file_empty(self, tmp_path):
        """Test validating an empty file."""
        file_path = tmp_path / "empty.md"
        file_path.write_text("")
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is False
        assert len(result['issues']) == 1
        assert "empty" in result['issues'][0].lower()
    
    def test_validate_file_too_large(self, tmp_path):
        """Test validating a file that exceeds size limit."""
        file_path = tmp_path / "large.md"
        # Create a file larger than 50MB
        large_content = "x" * (51 * 1024 * 1024)
        file_path.write_text(large_content)
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is False
        assert len(result['issues']) == 1
        assert "exceeds maximum size" in result['issues'][0]
    
    def test_validate_file_large_warning(self, tmp_path):
        """Test that large files (>10MB) generate warnings."""
        file_path = tmp_path / "large.md"
        # Create a file between 10MB and 50MB
        large_content = "x" * (11 * 1024 * 1024)
        file_path.write_text(large_content)
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is True
        assert len(result['warnings']) == 1
        assert "large" in result['warnings'][0].lower()
    
    def test_validate_file_unsupported_format(self, tmp_path):
        """Test validating a file with unsupported extension."""
        file_path = tmp_path / "test.pdf"
        file_path.write_text("Not really a PDF")
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        assert result['valid'] is False
        assert len(result['issues']) == 1
        assert "unsupported file format" in result['issues'][0].lower()
    
    def test_validate_file_supported_extensions(self, tmp_path):
        """Test that all supported extensions are accepted."""
        supported = ['.md', '.html', '.htm', '.rst', '.txt', '.dml', '.py']
        service = BatchIngestService(None, None, None)
        
        for ext in supported:
            file_path = tmp_path / f"test{ext}"
            file_path.write_text("Test content")
            
            result = service.validate_file(file_path)
            assert result['valid'] is True, f"Extension {ext} should be valid"
    
    def test_validate_file_not_readable(self, tmp_path):
        """Test validating a file without read permissions."""
        import os
        import stat
        
        file_path = tmp_path / "noperm.md"
        file_path.write_text("Test content")
        
        # Remove read permissions
        os.chmod(file_path, stat.S_IWRITE)
        
        service = BatchIngestService(None, None, None)
        result = service.validate_file(file_path)
        
        # Restore permissions for cleanup
        os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE)
        
        assert result['valid'] is False
        assert any("not readable" in issue.lower() for issue in result['issues'])


class TestProgressTracking:
    """Test progress tracking functionality."""
    
    def test_load_progress_nonexistent_file(self, tmp_path):
        """Test loading progress when file doesn't exist."""
        progress_file = tmp_path / "progress.json"
        service = BatchIngestService(None, None, None)
        
        completed = service._load_progress(progress_file)
        
        assert completed == set()
    
    def test_save_and_load_progress(self, tmp_path):
        """Test saving and loading progress."""
        progress_file = tmp_path / "progress.json"
        service = BatchIngestService(None, None, None)
        
        # Save some files
        service._save_progress(progress_file, "/path/to/file1.md")
        service._save_progress(progress_file, "/path/to/file2.md")
        
        # Load progress
        completed = service._load_progress(progress_file)
        
        assert len(completed) == 2
        assert "/path/to/file1.md" in completed
        assert "/path/to/file2.md" in completed
    
    def test_save_progress_creates_file(self, tmp_path):
        """Test that saving progress creates the file."""
        progress_file = tmp_path / "progress.json"
        service = BatchIngestService(None, None, None)
        
        assert not progress_file.exists()
        
        service._save_progress(progress_file, "/path/to/file.md")
        
        assert progress_file.exists()
    
    def test_save_progress_no_duplicates(self, tmp_path):
        """Test that saving same file twice doesn't create duplicates."""
        progress_file = tmp_path / "progress.json"
        service = BatchIngestService(None, None, None)
        
        # Save same file twice
        service._save_progress(progress_file, "/path/to/file.md")
        service._save_progress(progress_file, "/path/to/file.md")
        
        # Load progress
        completed = service._load_progress(progress_file)
        
        assert len(completed) == 1
        assert "/path/to/file.md" in completed
    
    def test_load_progress_corrupted_file(self, tmp_path):
        """Test loading progress from corrupted JSON file."""
        progress_file = tmp_path / "progress.json"
        progress_file.write_text("not valid json {{{")
        
        service = BatchIngestService(None, None, None)
        completed = service._load_progress(progress_file)
        
        # Should return empty set on corrupted file
        assert completed == set()
    
    def test_progress_file_format(self, tmp_path):
        """Test that progress file has correct format."""
        import json
        
        progress_file = tmp_path / "progress.json"
        service = BatchIngestService(None, None, None)
        
        service._save_progress(progress_file, "/path/to/file.md")
        
        # Read and verify format
        with open(progress_file, 'r') as f:
            data = json.load(f)
        
        assert 'version' in data
        assert 'completed_files' in data
        assert 'last_updated' in data
        assert data['version'] == '1.0'
        assert isinstance(data['completed_files'], list)


class TestErrorReporting:
    """Test error reporting functionality."""
    
    def test_generate_error_report(self, tmp_path):
        """Test generating error report file."""
        import json
        
        service = BatchIngestService(None, None, None)
        errors = [
            {'file': '/path/file1.md', 'type': 'validation', 'issues': ['File too large']},
            {'file': '/path/file2.md', 'type': 'processing', 'error': 'Parse error'},
        ]
        
        output_path = tmp_path / "errors.json"
        service._generate_error_report(errors, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert 'timestamp' in report
        assert report['total_errors'] == 2
        assert 'error_summary' in report
        assert report['errors'] == errors
    
    def test_error_report_summary(self, tmp_path):
        """Test error report includes summary by type."""
        import json
        
        service = BatchIngestService(None, None, None)
        errors = [
            {'file': '/path/file1.md', 'type': 'validation', 'issues': []},
            {'file': '/path/file2.md', 'type': 'validation', 'issues': []},
            {'file': '/path/file3.md', 'type': 'processing', 'error': ''},
        ]
        
        output_path = tmp_path / "errors.json"
        service._generate_error_report(errors, output_path)
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['error_summary']['validation'] == 2
        assert report['error_summary']['processing'] == 1


class TestBatchIngestion:
    """Test batch ingestion functionality."""
    
    def test_ingest_batch_dry_run(self, tmp_path):
        """Test batch ingestion in dry-run mode."""
        # Create test files
        (tmp_path / "file1.md").write_text("# Test 1")
        (tmp_path / "file2.md").write_text("# Test 2")
        (tmp_path / "invalid.pdf").write_text("Not supported")
        
        service = BatchIngestService(None, None, None)
        
        progress = service.ingest_batch(
            tmp_path,
            pattern="*.md,*.pdf",
            recursive=False,
            dry_run=True
        )
        
        assert progress.total_files == 3
        assert progress.processed == 3
        assert progress.succeeded == 2  # 2 valid markdown files
        assert progress.failed == 1  # 1 invalid PDF
    
    def test_ingest_batch_with_resume(self, tmp_path):
        """Test batch ingestion with resume capability."""
        import json
        
        # Create test files
        (tmp_path / "file1.md").write_text("# Test 1")
        (tmp_path / "file2.md").write_text("# Test 2")
        (tmp_path / "file3.md").write_text("# Test 3")
        
        # Manually create a progress file simulating a previous interrupted run
        progress_file = tmp_path / ".batch_ingest_progress.json"
        completed_file = str((tmp_path / "file1.md").absolute())
        progress_data = {
            'version': '1.0',
            'completed_files': [completed_file],
            'last_updated': '2025-01-01T00:00:00'
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
        
        # Create mock ingest service
        class MockIngestService:
            def __init__(self):
                self.processed_files = []
            
            def ingest_document(self, file_path, force_reprocess=False):
                self.processed_files.append(file_path)
                return {
                    'success': True,
                    'file_id': 'test_id',
                    'chunks_created': 5,
                    'word_count': 100,
                    'processing_time': 0.1
                }
        
        mock_ingest = MockIngestService()
        service = BatchIngestService(None, None, mock_ingest)
        
        # Run with resume - should skip file1, process file2 and file3
        progress = service.ingest_batch(tmp_path, pattern="*.md", recursive=False, resume=True)
        
        assert progress.total_files == 3
        assert progress.skipped == 1  # file1 was skipped
        assert progress.succeeded == 2  # file2 and file3 processed
        assert len(mock_ingest.processed_files) == 2  # Only 2 files actually processed
        assert completed_file not in mock_ingest.processed_files  # file1 was not processed
    
    def test_ingest_batch_error_handling(self, tmp_path):
        """Test that batch ingestion continues after errors."""
        # Create test files
        (tmp_path / "file1.md").write_text("# Test 1")
        (tmp_path / "empty.md").write_text("")  # Invalid - empty
        (tmp_path / "file2.md").write_text("# Test 2")
        
        class MockIngestService:
            def ingest_document(self, file_path, force_reprocess=False):
                return {
                    'success': True,
                    'file_id': 'test_id',
                    'chunks_created': 5,
                    'word_count': 100,
                    'processing_time': 0.1
                }
        
        service = BatchIngestService(None, None, MockIngestService())
        
        progress = service.ingest_batch(tmp_path, pattern="*.md", recursive=False)
        
        # Should process all files despite error
        assert progress.total_files == 3
        assert progress.processed == 3
        assert progress.succeeded == 2  # 2 valid files
        assert progress.failed == 1  # 1 empty file
        assert len(progress.errors) == 1
    
    def test_ingest_batch_generates_error_report(self, tmp_path):
        """Test that error report is generated when errors occur."""
        # Create invalid file
        (tmp_path / "empty.md").write_text("")
        
        service = BatchIngestService(None, None, None)
        
        progress = service.ingest_batch(tmp_path, pattern="*.md", recursive=False, dry_run=True)
        
        # Check error report was created
        error_report = tmp_path / "batch_ingest_errors.json"
        assert error_report.exists()
    
    def test_ingest_batch_removes_progress_file_on_completion(self, tmp_path):
        """Test that progress file is removed when batch completes."""
        # Create test file
        (tmp_path / "file1.md").write_text("# Test")
        
        class MockIngestService:
            def ingest_document(self, file_path, force_reprocess=False):
                return {
                    'success': True,
                    'file_id': 'test_id',
                    'chunks_created': 5,
                    'word_count': 100,
                    'processing_time': 0.1
                }
        
        service = BatchIngestService(None, None, MockIngestService())
        
        progress = service.ingest_batch(tmp_path, pattern="*.md", recursive=False)
        
        # Progress file should be removed after completion
        progress_file = tmp_path / ".batch_ingest_progress.json"
        assert not progress_file.exists()
    
    def test_ingest_batch_force_reprocess(self, tmp_path):
        """Test batch ingestion with force reprocess flag."""
        # Create test file
        (tmp_path / "file1.md").write_text("# Test")
        
        class MockIngestService:
            def __init__(self):
                self.force_called = False
            
            def ingest_document(self, file_path, force_reprocess=False):
                self.force_called = force_reprocess
                return {
                    'success': True,
                    'file_id': 'test_id',
                    'chunks_created': 5,
                    'word_count': 100,
                    'processing_time': 0.1
                }
        
        mock_ingest = MockIngestService()
        service = BatchIngestService(None, None, mock_ingest)
        
        progress = service.ingest_batch(tmp_path, pattern="*.md", recursive=False, force=True)
        
        assert mock_ingest.force_called is True


class TestBatchProgress:
    """Test BatchProgress dataclass."""
    
    def test_batch_progress_initialization(self):
        """Test BatchProgress initialization."""
        progress = BatchProgress(total_files=10)
        
        assert progress.total_files == 10
        assert progress.processed == 0
        assert progress.succeeded == 0
        assert progress.failed == 0
        assert progress.skipped == 0
        assert progress.errors == []
        assert isinstance(progress.start_time, datetime)
    
    def test_batch_progress_percent_calculation(self):
        """Test progress percentage calculation."""
        progress = BatchProgress(total_files=10, processed=5)
        
        assert progress.progress_percent == 50.0
    
    def test_batch_progress_percent_zero_total(self):
        """Test progress percentage with zero total files."""
        progress = BatchProgress(total_files=0)
        
        assert progress.progress_percent == 0.0
    
    def test_batch_progress_percent_complete(self):
        """Test progress percentage when complete."""
        progress = BatchProgress(total_files=10, processed=10)
        
        assert progress.progress_percent == 100.0
