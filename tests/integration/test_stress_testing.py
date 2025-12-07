"""
Stress tests for batch processing system.
Tests large file processing, memory management, and error recovery.
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

from core.services.batch_ingest_service import BatchIngestService, BatchProgress
from core.config.batch_config import BatchConfig


class TestStressTesting:
    """Stress tests for batch processing."""
    
    @pytest.fixture
    def stress_config(self):
        """Create configuration optimized for stress testing."""
        config = BatchConfig()
        config.chunk_processing_size = 50
        config.max_retry_attempts = 2
        config.memory_threshold_mb = 512
        config.progress_save_interval = 25
        return config
    
    @pytest.fixture
    def mock_services_stress(self):
        """Create mock services for stress testing."""
        backend = Mock()
        git_service = Mock()
        ingest_service = Mock()
        return backend, git_service, ingest_service
    
    @pytest.fixture
    def batch_service_stress(self, mock_services_stress, stress_config):
        """Create batch service with stress test configuration."""
        backend, git_service, ingest_service = mock_services_stress
        service = BatchIngestService(backend, git_service, ingest_service)
        service.config = stress_config
        return service
    
    @pytest.fixture
    def large_file_directory(self):
        """Create directory with many test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create many files for stress testing
            for i in range(500):  # 500 files
                file_path = temp_path / f"stress_test_{i:04d}.md"
                content = f"# Stress Test File {i}\n\n" + "Content line. " * 100
                file_path.write_text(content)
            
            # Create some large files
            for i in range(5):
                large_file = temp_path / f"large_stress_{i}.md"
                large_content = f"# Large Stress File {i}\n\n" + "Large content block. " * 5000
                large_file.write_text(large_content)
            
            # Create files with different extensions
            for ext in ['.rst', '.txt', '.py']:
                for i in range(10):
                    file_path = temp_path / f"mixed_{i:02d}{ext}"
                    file_path.write_text(f"Content for {ext} file {i}")
            
            yield temp_path
    
    @pytest.mark.slow
    def test_large_batch_processing(self, batch_service_stress, large_file_directory, mock_services_stress):
        """Test processing large number of files."""
        _, _, ingest_service = mock_services_stress
        
        # Mock successful processing with slight delay to simulate real work
        def mock_ingest(file_path, force_reprocess=False):
            time.sleep(0.001)  # 1ms delay per file
            return {'success': True}
        
        ingest_service.ingest_document.side_effect = mock_ingest
        
        start_time = time.time()
        
        # Process all markdown files
        result = batch_service_stress.ingest_batch(
            large_file_directory,
            pattern="*.md",
            recursive=False,
            force=False,
            dry_run=False,
            resume=False
        )
        
        processing_time = time.time() - start_time
        
        # Verify processing completed successfully
        assert result.total_files == 505  # 500 + 5 large files
        assert result.succeeded == 505
        assert result.failed == 0
        assert result.skipped == 0
        
        # Verify performance metrics
        assert result.files_per_second > 0
        assert processing_time < 60  # Should complete within reasonable time
        
        # Verify memory tracking
        assert result.memory_usage_mb > 0
        assert result.peak_memory_mb >= result.memory_usage_mb
        
        print(f"Processed {result.total_files} files in {processing_time:.2f}s "
              f"({result.files_per_second:.1f} files/sec)")
    
    @pytest.mark.slow
    def test_memory_pressure_handling(self, batch_service_stress, large_file_directory):
        """Test behavior under memory pressure."""
        
        # Monitor memory usage during processing
        memory_readings = []
        
        def monitor_memory():
            import psutil
            process = psutil.Process()
            while True:
                try:
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    memory_readings.append(memory_mb)
                    time.sleep(0.1)
                except psutil.NoSuchProcess:
                    break
        
        # Start memory monitoring thread
        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()
        
        # Process files (using dry run for faster execution)
        result = batch_service_stress.ingest_batch(
            large_file_directory,
            pattern="*.md",
            recursive=False,
            dry_run=True  # Faster execution for memory test
        )
        
        # Allow some time for memory monitoring
        time.sleep(0.5)
        
        # Verify memory stayed within reasonable bounds
        if memory_readings:
            max_memory = max(memory_readings)
            print(f"Peak memory usage: {max_memory:.1f}MB")
            
            # Memory should not grow excessively (adjust threshold based on system)
            assert max_memory < 2048  # 2GB threshold (adjust as needed)
    
    def test_concurrent_access_simulation(self, batch_service_stress, large_file_directory, mock_services_stress):
        """Test handling of concurrent-like access patterns."""
        _, _, ingest_service = mock_services_stress
        
        # Simulate variable processing times and occasional failures
        call_count = 0
        def variable_mock_ingest(file_path, force_reprocess=False):
            nonlocal call_count
            call_count += 1
            
            # Simulate variable processing times
            if call_count % 10 == 0:
                time.sleep(0.01)  # Slower processing occasionally
            
            # Simulate occasional failures (5% failure rate)
            if call_count % 20 == 0:
                raise RuntimeError("Simulated processing failure")
            
            return {'success': True}
        
        ingest_service.ingest_document.side_effect = variable_mock_ingest
        
        # Process subset of files with variable patterns
        result = batch_service_stress.ingest_batch(
            large_file_directory,
            pattern="stress_test_*.md",
            recursive=False,
            force=False,
            dry_run=False,
            resume=False
        )
        
        # Should handle failures gracefully
        assert result.total_files > 0
        assert result.succeeded > 0
        # Some failures expected due to simulated errors
        assert result.failed > 0
        
        # Total processed should equal succeeded + failed
        assert result.processed == result.succeeded + result.failed + result.skipped
    
    def test_progress_file_corruption_recovery_stress(self, batch_service_stress, large_file_directory):
        """Test progress file corruption recovery under stress."""
        
        # Create directory with many files
        files = list(large_file_directory.glob("*.md"))[:100]  # Use subset for faster test
        
        # Simulate progress file corruption during processing
        progress_file = large_file_directory / ".batch_ingest_progress.json"
        
        # Create initial valid progress
        initial_progress = {
            "version": "1.0",
            "completed_files": [str(f) for f in files[:20]],  # 20 files "completed"
            "last_updated": "2025-01-01T00:00:00"
        }
        
        import json
        with open(progress_file, 'w') as f:
            json.dump(initial_progress, f)
        
        # Corrupt the file
        with open(progress_file, 'w') as f:
            f.write('{"completed_files": ["file1.md", "file2.md" invalid json}')
        
        # Should recover gracefully
        recovered = batch_service_stress._load_progress(progress_file)
        
        assert isinstance(recovered, set)
        # Should have created backup
        backup_file = progress_file.with_suffix('.backup')
        assert backup_file.exists()
    
    def test_error_accumulation_stress(self, batch_service_stress, large_file_directory, mock_services_stress):
        """Test error handling with many failures."""
        _, _, ingest_service = mock_services_stress
        
        # Mock high failure rate
        call_count = 0
        def high_failure_mock(file_path, force_reprocess=False):
            nonlocal call_count
            call_count += 1
            
            # 50% failure rate
            if call_count % 2 == 0:
                raise ValueError(f"Simulated error for file {call_count}")
            
            return {'success': True}
        
        ingest_service.ingest_document.side_effect = high_failure_mock
        
        # Process files with high failure rate
        result = batch_service_stress.ingest_batch(
            large_file_directory,
            pattern="stress_test_*.md",  # Use subset
            recursive=False,
            force=False,
            dry_run=False,
            resume=False
        )
        
        # Should handle many errors without crashing
        assert result.total_files > 0
        assert result.failed > 0
        assert len(result.errors) == result.failed
        
        # Error report should be generated
        error_report = large_file_directory / "batch_ingest_errors.json"
        assert error_report.exists()
        
        # Verify error report structure
        with open(error_report) as f:
            error_data = json.load(f)
        
        assert 'timestamp' in error_data
        assert 'total_errors' in error_data
        assert 'errors' in error_data
        assert error_data['total_errors'] == len(error_data['errors'])
    
    def test_file_size_validation_stress(self, batch_service_stress, stress_config):
        """Test file size validation with various file sizes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files of various sizes
            test_cases = [
                ("empty.md", ""),  # Empty file
                ("tiny.md", "Small content"),  # Tiny file
                ("normal.md", "Normal content. " * 1000),  # Normal file
                ("large.md", "Large content. " * 100000),  # Large but acceptable file
            ]
            
            # Create very large file that exceeds limits
            huge_content = "Huge content. " * 1000000  # Very large
            huge_file = temp_path / "huge.md"
            huge_file.write_text(huge_content)
            
            for filename, content in test_cases:
                file_path = temp_path / filename
                file_path.write_text(content)
            
            # Test validation on all files
            valid_count = 0
            invalid_count = 0
            
            for file_path in temp_path.glob("*.md"):
                result = batch_service_stress.validate_file(file_path)
                if result['valid']:
                    valid_count += 1
                else:
                    invalid_count += 1
            
            # Should have some valid and some invalid files
            assert valid_count > 0  # Normal files should be valid
            assert invalid_count > 0  # Empty and huge files should be invalid
    
    @pytest.mark.slow
    def test_full_stress_scenario(self, batch_service_stress, large_file_directory, mock_services_stress):
        """Full stress test combining multiple challenging conditions."""
        _, _, ingest_service = mock_services_stress
        
        # Complex mock that simulates real-world variability
        call_count = 0
        def complex_mock_ingest(file_path, force_reprocess=False):
            nonlocal call_count
            call_count += 1
            
            # Variable processing times
            if call_count % 5 == 0:
                time.sleep(0.002)  # Slower processing
            elif call_count % 17 == 0:
                time.sleep(0.005)  # Even slower occasionally
            
            # Various failure modes
            if call_count % 50 == 0:
                raise RuntimeError("Network timeout simulation")
            elif call_count % 73 == 0:
                raise ValueError("Parse error simulation")
            elif call_count % 101 == 0:
                return {'success': False, 'error': 'Validation failed'}
            
            return {'success': True}
        
        ingest_service.ingest_document.side_effect = complex_mock_ingest
        
        # Run with resume capability
        start_time = time.time()
        
        result = batch_service_stress.ingest_batch(
            large_file_directory,
            pattern="*.md,*.rst,*.txt",  # Multiple patterns
            recursive=False,
            force=False,
            dry_run=False,
            resume=True
        )
        
        processing_time = time.time() - start_time
        
        # Should complete despite various failures
        assert result.total_files > 0
        assert result.processed == result.total_files
        assert result.succeeded + result.failed + result.skipped == result.total_files
        
        # Should have performance metrics
        assert result.files_per_second > 0
        assert result.peak_memory_mb > 0
        
        # Should have generated reports
        perf_report = large_file_directory / "batch_ingest_performance.json"
        assert perf_report.exists()
        
        if result.failed > 0:
            error_report = large_file_directory / "batch_ingest_errors.json"
            assert error_report.exists()
        
        print(f"Stress test completed: {result.succeeded} succeeded, "
              f"{result.failed} failed, {result.skipped} skipped in {processing_time:.2f}s")