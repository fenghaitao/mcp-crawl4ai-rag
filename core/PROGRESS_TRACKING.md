# Progress Tracking for Simics Source Code Crawling

## Overview

The Simics source code crawler now includes a **persistent progress tracking system** that maintains a checklist of all files being processed. This allows the crawler to:

- ✅ Resume from where it left off after interruptions
- ✅ Skip already completed files
- ✅ Track which files failed and why
- ✅ Export human-readable checklists
- ✅ Show real-time statistics

## How It Works

### The 5-Step Processing Pipeline

Each file goes through 5 steps:

1. **File Summary** - Generate a summary of the entire file
2. **Chunking** - Break the file into semantic chunks using AST
3. **Chunk Summaries** - Generate summaries for each chunk
4. **Prepare Embedding** - Prepare data for vector embeddings
5. **Upload** - Create embeddings and upload to Supabase

### Progress Storage

Progress is stored in:
```
progress/
├── simics_crawl_progress.json      # Detailed progress data
├── simics_crawl_progress.json.lock # File lock for concurrent access
└── checklist.txt                   # Human-readable checklist
```

### Data Structure

Each file entry contains:
```json
{
  "file_path": "/path/to/file.dml",
  "name": "/path/to/file.dml",
  "completed": true,
  "steps_completed": ["file_summary", "chunking", "chunk_summaries", "prepare_embedding", "upload"],
  "total_steps": 5,
  "chunks_created": 15,
  "chunks_uploaded": 15,
  "added_at": "2025-12-01T10:00:00",
  "last_updated": "2025-12-01T10:05:30",
  "completed_at": "2025-12-01T10:05:30",
  "error": null
}
```

## Usage

### Normal Operation

Simply run the crawler as usual:
```bash
python scripts/crawl_simics_source.py
```

The progress tracker will:
- Load existing progress on startup
- Show a summary of completed/pending files
- Skip files that are already completed
- Save progress after each file
- Export a checklist at the end

### View Progress Summary

At startup and completion, you'll see:
```
============================================================
📊 Progress Summary
============================================================
   Total Files:      1234
   ✅ Completed:     567 (45.9%)
   ⏳ Pending:       600
   ❌ Failed:        67
   📦 Chunks Created: 8505
   💾 Chunks Uploaded: 8505
============================================================
```

### Resume After Interruption

If the crawler is interrupted (Ctrl+C, crash, etc.), simply run it again:
```bash
python scripts/crawl_simics_source.py
```

It will automatically:
- Load the previous progress
- Skip all completed files
- Continue from where it left off

### Retry Failed Files

Failed files are tracked with error messages. To retry them:

1. Check the checklist to see which files failed:
   ```bash
   cat progress/checklist.txt
   ```

2. The progress tracker will automatically retry failed files on the next run (they're marked as pending with error information)

### Reset Progress

To start fresh (process all files again):

```python
from progress_tracker import ProgressTracker

tracker = ProgressTracker()
tracker.reset_all()
```

Or manually delete the progress file:
```bash
rm progress/simics_crawl_progress.json
```

### View Checklist

The human-readable checklist is automatically exported to:
```
progress/checklist.txt
```

Example format:
```
Simics Source Code Crawling Checklist
Generated: 2025-12-01T10:30:00
================================================================================

Progress: 567/1234 (45.9%)

✅ COMPLETED (567 files)
--------------------------------------------------------------------------------
[✓] device.dml (15 chunks)
[✓] registers.dml (8 chunks)
[✓] interface.py (12 chunks)
...

⏳ PENDING (600 files)
--------------------------------------------------------------------------------
[ ] another_device.dml
[ ] utils.py
...

❌ FAILED (67 files)
--------------------------------------------------------------------------------
[✗] broken_file.dml
    Error: Syntax error in DML file

[✗] large_file.py
    Error: Timeout during chunking
...
```

## Command-Line Options

### Log Files with Progress Tracking

```bash
# Save detailed logs with timestamps
python scripts/crawl_simics_source.py --log-file logs/crawl_$(date +%Y%m%d_%H%M%S).log
```

### Force Re-processing

To force delete and re-process all files (ignores progress):
```bash
python scripts/crawl_simics_source.py --force-delete
```

## API Reference

### ProgressTracker Class

```python
from progress_tracker import ProgressTracker

tracker = ProgressTracker(progress_file="progress/simics_crawl_progress.json")

# Add files
tracker.add_file("path/to/file.dml")
tracker.add_files(["file1.py", "file2.dml"])

# Mark progress
tracker.mark_step_completed("path/to/file.dml", "file_summary")
tracker.mark_completed("path/to/file.dml", chunks_created=10, chunks_uploaded=10)
tracker.mark_failed("path/to/file.dml", "Error message")

# Check status
if tracker.is_completed("path/to/file.dml"):
    print("Already done!")

# Get statistics
stats = tracker.get_statistics()
print(f"Completed: {stats['completed']}/{stats['total_files']}")

# Export checklist
tracker.export_checklist("progress/checklist.txt")

# Show summary
tracker.print_summary()
```

### Step Names

The 5 steps are tracked with these names:
- `"file_summary"` - Step 1
- `"chunking"` - Step 2
- `"chunk_summaries"` - Step 3
- `"prepare_embedding"` - Step 4
- `"upload"` - Step 5

## Benefits

### Reliability
- **Crash Recovery**: Resume from any point without losing work
- **Network Failures**: Retry only failed files, not everything
- **Long-Running Jobs**: Track progress over days/weeks

### Efficiency
- **Skip Completed**: No wasted time re-processing finished files
- **Incremental Updates**: Only process new/changed files
- **Resource Optimization**: Better memory usage with per-file processing

### Visibility
- **Real-time Stats**: See completion percentage and ETA
- **Error Tracking**: Know exactly which files failed and why
- **Audit Trail**: Full history of when files were processed

## Examples

### Example 1: Initial Run

```bash
$ python scripts/crawl_simics_source.py

🚀 Starting Simics Source Code Crawling at 10:00:00
📁 Simics path: simics-7-packages-2025-38-linux64/

============================================================
📊 Progress Summary
============================================================
   Total Files:      0
   ✅ Completed:     0 (0%)
   ⏳ Pending:       0
   ❌ Failed:        0
   📦 Chunks Created: 0
   💾 Chunks Uploaded: 0
============================================================

🔍 Searching for source files...
   ✅ Found 800 DML files
   ✅ Found 434 Python files
➕ Added 1234 new files to progress tracker

[Processing files...]
```

### Example 2: Resume After Interruption

```bash
$ python scripts/crawl_simics_source.py

🚀 Starting Simics Source Code Crawling at 14:30:00
📁 Simics path: simics-7-packages-2025-38-linux64/

============================================================
📊 Progress Summary
============================================================
   Total Files:      1234
   ✅ Completed:     567 (45.9%)
   ⏳ Pending:       600
   ❌ Failed:        67
   📦 Chunks Created: 8505
   💾 Chunks Uploaded: 8505
============================================================

[Continuing from file 568...]

============================================================
⏭️  [568/1234] already_done.dml
   ✅ Already completed - skipping

============================================================
📄 [569/1234] next_file.dml
   Source: simics-dml | Type: DML | Size: 4523 chars
   📝 Step 1: Generating file summary...
   ...
```

### Example 3: View Final Results

```bash
$ cat progress/checklist.txt

Simics Source Code Crawling Checklist
Generated: 2025-12-01T16:45:23
================================================================================

Progress: 1234/1234 (100.0%)

✅ COMPLETED (1234 files)
--------------------------------------------------------------------------------
[✓] device1.dml (15 chunks)
[✓] device2.dml (8 chunks)
[✓] interface.py (12 chunks)
[✓] utils.py (5 chunks)
...
```

## Troubleshooting

### Progress File Corrupted

If the progress file gets corrupted:
```bash
# Backup the old file
mv progress/simics_crawl_progress.json progress/backup.json

# Start fresh
python scripts/crawl_simics_source.py
```

### Lock File Issues

If you see lock file errors:
```bash
# Remove stale lock file
rm progress/simics_crawl_progress.json.lock
```

### Reset Specific Failed Files

To reset only failed files to pending:
```python
from progress_tracker import ProgressTracker

tracker = ProgressTracker()
tracker.reset_failed_files()
```

## Architecture

The progress tracker is designed to be:
- **Thread-safe**: Uses file locking for concurrent access
- **Crash-resistant**: Saves after each file completion
- **Memory-efficient**: Only loads tracking data, not file contents
- **Human-readable**: JSON format for easy inspection/editing

## Future Enhancements

Potential improvements:
- Web dashboard for progress visualization
- Parallel processing with distributed progress tracking
- Integration with CI/CD pipelines
- Automatic retry strategies for failed files
- Performance metrics (processing time per file)
