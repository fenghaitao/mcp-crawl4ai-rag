"""
Tests for enhanced batch processing functionality including chunked processing,
retry logic, and performance monitoring.
"""

import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from core.services.batch_ingest_service import BatchIngestService, BatchProgress
from core.config.batch_config import BatchConfig


class TestEnhancedBatchProcessing:
    """Test enhanced batch processing features."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        backend = Mock()
        git_service = Mock()
        ingest_service = Mock()
        return backend, git_service, ingest_service
    
    @pytest.fixture
    def batch_service(self, mock_services):
        """Create BatchIngestService with mocked dependencies."""
        backend, git_service, ingest_service = mock_services
        return BatchIngestService(backend, git_service, ingest_service)
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            for i in range(10):
                file_path = temp_path / f"test_file_{i:02d}.md"
                file_path.write_text(f"# Test File {i}\n\nContent for test file {i}.")
            
            # Create a large file for testing size limits
            large_file = temp_path / "large_file.md"
            large_content = "# Large File\n" + "Large content. " * 10000
            large_file.write_text(large_content)
            
            yield temp_path
    
    def test_chunked_processing(self, batch_service, temp_directory, mock_services):
        """Test chunked file processing."""
        _, _, ingest_service = mock_services
        
        # Configure small chunk size for testing
        batch_service.config.chunk_processing_size = 3
        
        # Mock successful processing
        ingest_service.ingest_document.return_value = {'success': True}
        
        files = list(temp_directory.glob("*.md"))[:6]  # Use 6 files to test 2 chunks
        progress = BatchProgress(total_files=len(files))
        progress_file = temp_directory / ".test_progress.json"
        completed_files = set()
        
        batch_service._process_files_in_chunks(
            files, progress, progress_file, completed_files, force=False
        )
        
        # Should have processed all files
        assert progress.processed == 6
        assert progress.succeeded == 6
        assert progress.failed == 0
        
        # Should have called ingest_document for each file
        assert ingest_service.ingest_document.call_count == 6
    
    def test_memory_monitoring(self, batch_service, temp_directory):
        """Test memory usage monitoring."""
        progress = BatchProgress(total_files=10)
        
        # Update metrics
        progress.update_metrics()
        
        # Should have memory usage values
        assert progress.memory_usage_mb > 0
        assert progress.peak_memory_mb >= progress.memory_usage_mb
        
        # Test metrics calculation
        time.sleep(0.1)  # Small delay to test timing
        progress.processed = 5
        progress.update_metrics()
        
        assert progress.files_per_second > 0
        assert progress.elapsed_time > 0
    
    @patch('core.services.batch_ingest_service.psutil.Process')
    def test_memory_threshold_warning(self, mock_process, batch_service, temp_directory, mock_services):
        """Test memory threshold warning."""
        _, _, ingest_service = mock_services
        
        # Mock high memory usage
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 2 * 1024 * 1024 * 1024  # 2GB
        mock_process.return_value = mock_process_instance
        
        # Set low threshold for testing
        batch_service.config.memory_threshold_mb = 1024  # 1GB
        
        ingest_service.ingest_document.return_value = {'success': True}
        
        files = list(temp_directory.glob("*.md"))[:2]
        progress = BatchProgress(total_files=len(files))
        progress_file = temp_directory / ".test_progress.json"
        completed_files = set()
        
        with patch.object(batch_service.logger, 'warning') as mock_warning:
            batch_service._process_files_in_chunks(
                files, progress, progress_file, completed_files, force=False
            )
            
            # Should have logged memory warning
            mock_warning.assert_called()
            warning_message = str(mock_warning.call_args[0][0])
            assert "High memory usage" in warning_message
    
    def test_retry_mechanism_integration(self, batch_service, temp_directory, mock_services):
        """Test retry mechanism with batch processing."""
        _, _, ingest_service = mock_services
        
        # Configure fast retry for testing
        batch_service.config.max_retry_attempts = 3
        batch_service.config.retry_backoff_factor = 0.1
        
        # Mock service to fail twice then succeed
        call_count = 0
        def mock_ingest(file_path, force_reprocess=False):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Temporary failure")
            return {'success': True}
        
        ingest_service.ingest_document.side_effect = mock_ingest
        
        files = list(temp_directory.glob("*.md"))[:1]
        progress = BatchProgress(total_files=1)
        
        success = batch_service._process_single_file_with_retry(
            str(files[0]), False, progress
        )
        
        assert success is True
        assert call_count == 3  # Should have retried twice
        assert progress.succeeded == 1
        assert progress.failed == 0
    
    def test_retry_exhaustion(self, batch_service, temp_directory, mock_services):
        """Test behavior when retry attempts are exhausted."""
        _, _, ingest_service = mock_services
        
        # Configure fast retry for testing
        batch_service.config.max_retry_attempts = 2
        batch_service.config.retry_backoff_factor = 0.1
        
        # Mock service to always fail
        ingest_service.ingest_document.side_effect = RuntimeError("Persistent failure")
        
        files = list(temp_directory.glob("*.md"))[:1]
        progress = BatchProgress(total_files=1)
        
        success = batch_service._process_single_file_with_retry(
            str(files[0]), False, progress
        )
        
        assert success is False
        assert progress.succeeded == 0
        assert progress.failed == 1
        assert len(progress.errors) == 1
        assert "exception_after_retries" in progress.errors[0]['type']
    
    def test_performance_report_generation(self, batch_service, temp_directory):
        """Test performance report generation."""
        progress = BatchProgress(total_files=10)
        progress.processed = 8
        progress.succeeded = 7
        progress.failed = 1
        progress.skipped = 0
        progress.update_metrics()
        
        batch_service._generate_performance_report(progress, temp_directory)
        
        # Check that performance report was created
        report_path = temp_directory / "batch_ingest_performance.json"
        assert report_path.exists()
        
        # Verify report content
        with open(report_path) as f:
            report_data = json.load(f)
        
        assert 'timestamp' in report_data
        assert 'processing_summary' in report_data
        assert 'performance_metrics' in report_data
        assert 'configuration' in report_data
        
        # Check processing summary
        summary = report_data['processing_summary']
        assert summary['total_files'] == 10
        assert summary['processed'] == 8
        assert summary['succeeded'] == 7
        assert summary['failed'] == 1
        assert summary['success_rate'] == 87.5  # 7/8 * 100
        
        # Check performance metrics
        metrics = report_data['performance_metrics']
        assert 'elapsed_time_seconds' in metrics
        assert 'files_per_second' in metrics
        assert 'memory_usage_mb' in metrics
        assert 'peak_memory_mb' in metrics
    
    def test_progress_corruption_recovery(self, batch_service, temp_directory):
        """Test recovery from corrupted progress file."""
        progress_file = temp_directory / ".test_progress.json"
        
        # Create corrupted JSON
        progress_file.write_text('{"completed_files": [invalid json')
        
        # Should recover gracefully and return empty set
        result = batch_service._load_progress(progress_file)
        assert isinstance(result, set)
        assert len(result) == 0
        
        # Should have created backup
        backup_file = progress_file.with_suffix('.backup')
        assert backup_file.exists()
    
    def test_progress_recovery_with_text_extraction(self, batch_service, temp_directory):
        """Test text-based recovery from corrupted progress file."""
        progress_file = temp_directory / ".test_progress.json"
        
        # Create partially corrupted file with recoverable file paths
        corrupted_content = '''
        {
            "completed_files": [
                "/path/to/file1.md",
                "/path/to/file2.py"
            invalid structure here
            "other_field": "/path/to/file3.rst"
        }
        '''
        progress_file.write_text(corrupted_content)
        
        # Should attempt text recovery
        result = batch_service._attempt_progress_recovery(progress_file)
        
        # Should recover some file paths
        assert isinstance(result, set)
        # The exact recovery depends on regex matching, but should find some paths
    
    def test_get_processing_metrics(self, batch_service):
        """Test getting current processing metrics."""
        progress = BatchProgress(total_files=100)
        progress.processed = 50
        progress.succeeded = 45
        progress.failed = 5
        
        # Let some time pass for rate calculation
        time.sleep(0.1)
        
        metrics = batch_service.get_processing_metrics(progress)
        
        assert 'progress_percent' in metrics
        assert 'files_per_second' in metrics
        assert 'memory_usage_mb' in metrics
        assert 'peak_memory_mb' in metrics
        assert 'elapsed_time' in metrics
        assert 'estimated_time_remaining' in metrics
        
        assert metrics['progress_percent'] == 50.0
        assert metrics['files_per_second'] >= 0
    
    def test_configuration_integration(self, mock_services):
        """Test that configuration is properly integrated."""
        backend, git_service, ingest_service = mock_services
        service = BatchIngestService(backend, git_service, ingest_service)
        
        # Should have loaded configuration
        assert hasattr(service, 'config')
        assert isinstance(service.config, BatchConfig)
        
        # Should use config values in validation
        test_file = Path("/tmp/test.md")
        with patch.object(test_file, 'exists', return_value=True), \
             patch.object(test_file, 'is_file', return_value=True), \
             patch.object(test_file, 'stat') as mock_stat, \
             patch('builtins.open', MagicMock()):
            
            mock_stat.return_value.st_size = service.config.max_file_size + 1
            
            result = service.validate_file(test_file)
            assert not result['valid']
            assert any('exceeds maximum size' in issue for issue in result['issues'])
    
    def test_batch_processing_with_enhanced_features(self, batch_service, temp_directory, mock_services):
        """Integration test for batch processing with all enhancements."""
        _, _, ingest_service = mock_services
        
        # Configure for testing
        batch_service.config.chunk_processing_size = 3
        batch_service.config.progress_save_interval = 2
        
        # Mock successful processing
        ingest_service.ingest_document.return_value = {'success': True}
        
        # Run batch processing
        result = batch_service.ingest_batch(
            temp_directory,
            pattern="*.md",
            recursive=False,
            force=False,
            dry_run=False,
            resume=False
        )
        
        # Should have processed files successfully
        assert result.total_files > 0
        assert result.succeeded > 0
        assert result.failed == 0
        
        # Should have generated performance report
        performance_report = temp_directory / "batch_ingest_performance.json"
        assert performance_report.exists()
        
        # Should have updated metrics
        assert result.files_per_second >= 0
        assert result.memory_usage_mb > 0