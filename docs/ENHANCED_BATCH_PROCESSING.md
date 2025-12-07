# Enhanced Batch Processing System

## Overview

The enhanced batch processing system provides significant improvements over the base implementation with advanced features for production environments including memory management, retry mechanisms, performance monitoring, and robust error recovery.

## Key Enhancements

### 1. Configuration Management

Centralized configuration system with environment variable support:

```python
from core.config.batch_config import BatchConfig, config

# Use global configuration
max_size = config.max_file_size

# Or create custom configuration
custom_config = BatchConfig.from_environment()
```

**Environment Variables:**
- `BATCH_MAX_FILE_SIZE`: Maximum file size in bytes (default: 50MB)
- `BATCH_MAX_BATCH_SIZE`: Maximum files per batch (default: 1000)
- `BATCH_PROGRESS_INTERVAL`: Progress save frequency (default: 10)
- `BATCH_MEMORY_THRESHOLD_MB`: Memory warning threshold (default: 1024MB)
- `BATCH_MAX_RETRIES`: Maximum retry attempts (default: 3)
- `BATCH_CHUNK_SIZE`: Chunk processing size (default: 100)

### 2. Chunked Processing

Files are processed in configurable chunks for better memory management:

```python
# Configuration
config.chunk_processing_size = 50  # Process 50 files per chunk

# Automatic chunked processing with memory monitoring
service.ingest_batch(directory, pattern="*.md")
```

**Benefits:**
- Reduced memory footprint for large batches
- Better progress granularity
- Improved error isolation
- Memory threshold warnings

### 3. Retry Mechanism

Robust retry logic for handling transient failures:

```python
from core.utils.retry import retry

@retry(max_attempts=3, backoff_factor=2.0)
def process_file():
    # Processing logic that may fail
    return result
```

**Features:**
- Configurable retry attempts and backoff
- Exponential backoff timing
- Specific exception filtering
- Retry callbacks for logging

### 4. Performance Monitoring

Comprehensive performance metrics and reporting:

```python
# Real-time metrics
metrics = service.get_processing_metrics(progress)
print(f"Rate: {metrics['files_per_second']:.1f} files/sec")
print(f"Memory: {metrics['memory_usage_mb']:.1f}MB")
print(f"ETA: {metrics['estimated_time_remaining']:.0f}s")

# Automatic performance report generation
# Creates: batch_ingest_performance.json
```

**Metrics Tracked:**
- Files processed per second
- Memory usage (current and peak)
- Processing success rate
- Estimated completion time
- Configuration parameters

### 5. Enhanced Error Recovery

Improved error handling and recovery mechanisms:

```python
# Progress file corruption recovery
completed_files = service._load_progress(progress_file)
# Automatically creates backups and attempts text recovery

# Enhanced error reporting with categorization
{
    "timestamp": "2025-01-15T10:30:00",
    "total_errors": 15,
    "error_summary": {
        "validation": 5,
        "processing": 8,
        "exception_after_retries": 2
    },
    "errors": [...]
}
```

## Usage Examples

### Basic Enhanced Processing

```python
from core.services.batch_ingest_service import BatchIngestService
from core.config.batch_config import config

# Configure for your environment
config.chunk_processing_size = 100
config.max_retry_attempts = 5
config.memory_threshold_mb = 2048

# Create service
service = BatchIngestService(backend, git_service, ingest_service)

# Process with all enhancements
result = service.ingest_batch(
    directory=Path("/docs"),
    pattern="*.md,*.rst,*.html",
    recursive=True,
    force=False,
    resume=True
)

# Check results
print(f"Success rate: {result.succeeded}/{result.total_files}")
print(f"Processing rate: {result.files_per_second:.1f} files/sec")
print(f"Peak memory: {result.peak_memory_mb:.1f}MB")
```

### Real-time Monitoring

```python
import time
from threading import Thread

def monitor_progress(service, progress):
    """Monitor processing progress in real-time."""
    while progress.processed < progress.total_files:
        metrics = service.get_processing_metrics(progress)
        
        print(f"\rProgress: {metrics['progress_percent']:.1f}% "
              f"({progress.processed}/{progress.total_files}) "
              f"Rate: {metrics['files_per_second']:.1f} files/sec "
              f"Memory: {metrics['memory_usage_mb']:.1f}MB "
              f"ETA: {metrics['estimated_time_remaining'] or 'N/A'}s", 
              end='')
        
        time.sleep(1)

# Start monitoring in separate thread
monitor_thread = Thread(target=monitor_progress, args=(service, progress))
monitor_thread.daemon = True
monitor_thread.start()

# Run processing
result = service.ingest_batch(directory, pattern="*.md")
```

### Custom Retry Configuration

```python
from core.utils.retry import retry

# Custom retry logic for specific operations
@retry(
    max_attempts=5,
    backoff_factor=1.5,
    exceptions=(ConnectionError, TimeoutError),
    on_retry=lambda e, attempt: print(f"Retry {attempt}: {e}")
)
def network_dependent_operation():
    # Operation that may fail due to network issues
    return api_call()
```

### Stress Testing Configuration

```python
# Configuration for high-throughput processing
stress_config = BatchConfig()
stress_config.chunk_processing_size = 200
stress_config.max_retry_attempts = 2
stress_config.memory_threshold_mb = 4096
stress_config.progress_save_interval = 50

# Apply configuration
service.config = stress_config

# Process large batches
result = service.ingest_batch(
    large_directory,
    pattern="*.md",
    recursive=True
)
```

## Performance Optimization

### Memory Management

1. **Chunk Size Tuning:**
   ```python
   # For high-memory systems
   config.chunk_processing_size = 500
   
   # For constrained environments
   config.chunk_processing_size = 25
   ```

2. **Memory Threshold Monitoring:**
   ```python
   config.memory_threshold_mb = 1024  # 1GB warning threshold
   ```

3. **Garbage Collection Hints:**
   ```python
   import gc
   
   # Force garbage collection between chunks
   # (automatically handled in enhanced version)
   gc.collect()
   ```

### Processing Speed

1. **Optimal Chunk Sizes:**
   - Small files (< 1KB): 500-1000 files per chunk
   - Medium files (1KB-100KB): 100-200 files per chunk  
   - Large files (> 100KB): 10-50 files per chunk

2. **Retry Configuration:**
   ```python
   # Fast retry for quick operations
   config.max_retry_attempts = 2
   config.retry_backoff_factor = 1.2
   
   # Robust retry for slow operations
   config.max_retry_attempts = 5
   config.retry_backoff_factor = 2.0
   ```

### Monitoring and Alerting

```python
def setup_monitoring(service, progress):
    """Setup monitoring with alerts."""
    
    def check_metrics():
        metrics = service.get_processing_metrics(progress)
        
        # Memory alert
        if metrics['memory_usage_mb'] > 2048:
            logger.warning(f"High memory usage: {metrics['memory_usage_mb']:.1f}MB")
        
        # Performance alert
        if metrics['files_per_second'] < 1.0:
            logger.warning(f"Low processing rate: {metrics['files_per_second']:.2f} files/sec")
    
    return check_metrics
```

## Error Handling Patterns

### Graceful Degradation

```python
try:
    result = service.ingest_batch(directory, pattern="*.md")
except MemoryError:
    # Reduce chunk size and retry
    service.config.chunk_processing_size = 10
    result = service.ingest_batch(directory, pattern="*.md")
except Exception as e:
    logger.error(f"Batch processing failed: {e}")
    # Fall back to single-file processing
```

### Error Analysis

```python
def analyze_errors(result):
    """Analyze processing errors for patterns."""
    error_types = {}
    
    for error in result.errors:
        error_type = error.get('type', 'unknown')
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    print("Error Summary:")
    for error_type, count in error_types.items():
        print(f"  {error_type}: {count}")
    
    return error_types
```

## Integration with Existing Systems

### CLI Integration

The enhanced features are automatically available through existing CLI commands:

```bash
# Standard batch processing with enhancements
python -m core.cli.main ingest-docs-batch /docs --pattern "*.md" --recursive

# Monitor progress in real-time
tail -f batch_ingest_performance.json

# Check error details
cat batch_ingest_errors.json | jq '.error_summary'
```

### Service Integration

```python
# Drop-in replacement for existing BatchIngestService
service = BatchIngestService(backend, git_service, ingest_service)

# All existing APIs work with enhancements
result = service.ingest_batch(directory, pattern="*.md")

# New APIs available
metrics = service.get_processing_metrics(result)
```

## Migration Guide

### From Basic to Enhanced

1. **Update Dependencies:**
   ```bash
   pip install psutil  # For memory monitoring
   ```

2. **Update Configuration:**
   ```python
   # Old
   MAX_FILE_SIZE = 50 * 1024 * 1024
   
   # New
   from core.config.batch_config import config
   max_size = config.max_file_size
   ```

3. **Update Error Handling:**
   ```python
   # Old
   try:
       result = process_file(path)
   except Exception:
       pass  # Silent failure
   
   # New - automatic retry
   result = service._process_single_file_with_retry(path, force, progress)
   ```

4. **Add Monitoring:**
   ```python
   # Add performance tracking
   metrics = service.get_processing_metrics(progress)
   ```

## Troubleshooting

### High Memory Usage

```python
# Check current memory
progress.update_metrics()
print(f"Memory: {progress.memory_usage_mb:.1f}MB")

# Reduce chunk size
service.config.chunk_processing_size = 25

# Lower memory threshold
service.config.memory_threshold_mb = 512
```

### Slow Processing

```python
# Check processing rate
metrics = service.get_processing_metrics(progress)
if metrics['files_per_second'] < 1.0:
    # Increase chunk size
    service.config.chunk_processing_size = 200
    
    # Reduce retries for faster failure
    service.config.max_retry_attempts = 2
```

### Frequent Failures

```python
# Analyze error patterns
error_types = analyze_errors(result)

# Adjust retry configuration
if 'network_error' in error_types:
    service.config.max_retry_attempts = 5
    service.config.retry_backoff_factor = 3.0
```

## Best Practices

1. **Configuration Management:**
   - Use environment variables for deployment-specific settings
   - Test configuration changes in development first
   - Monitor resource usage when adjusting limits

2. **Error Recovery:**
   - Always enable resume functionality for large batches
   - Review error reports for systematic issues
   - Set up alerting for high failure rates

3. **Performance Tuning:**
   - Profile memory usage with different chunk sizes
   - Monitor processing rates under various loads
   - Adjust configuration based on file characteristics

4. **Production Deployment:**
   - Set conservative memory thresholds initially
   - Enable comprehensive logging
   - Implement health checks for long-running processes

## API Reference

See individual class documentation for detailed API reference:

- [`BatchConfig`](core/config/batch_config.py) - Configuration management
- [`retry`](core/utils/retry.py) - Retry mechanism
- [`BatchIngestService`](core/services/batch_ingest_service.py) - Enhanced batch processing
- [`BatchProgress`](core/services/batch_ingest_service.py) - Progress tracking with metrics