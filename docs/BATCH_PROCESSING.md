# Batch Processing Guide

This guide explains how to use the batch processing features for ingesting multiple documentation files efficiently.

## Overview

The batch processing system allows you to:
- Ingest multiple files in a single command
- Track progress with resume capability
- Validate files before processing
- Handle errors gracefully
- Generate detailed error reports

## Basic Usage

### Batch Ingest Command

```bash
# Ingest all markdown files in a directory
simics-rag rag ingest-docs-batch /path/to/docs

# Ingest with custom pattern
simics-rag rag ingest-docs-batch /path/to/docs --pattern "*.md,*.html,*.rst"

# Non-recursive (current directory only)
simics-rag rag ingest-docs-batch /path/to/docs --no-recursive

# Force reprocess existing files
simics-rag rag ingest-docs-batch /path/to/docs --force

# Dry run (validate without processing)
simics-rag rag ingest-docs-batch /path/to/docs --dry-run

# Resume from previous progress
simics-rag rag ingest-docs-batch /path/to/docs --continue
```

## Features

### File Discovery

The system discovers files matching specified patterns:
- Supports multiple patterns: `*.md,*.html,*.rst`
- Recursive directory traversal (default)
- Filters by supported file extensions

### File Validation

Before processing, each file is validated for:
- **Existence and readability**: File must exist and be readable
- **Size limits**: 0 < size < 50MB
- **Format support**: Must be a supported file type (.md, .html, .htm, .rst, .txt, .dml, .py)

### Progress Tracking

The system tracks progress and can resume interrupted operations:
- Creates `.batch_ingest_progress.json` in the working directory
- Records completed files after successful processing
- Automatically removes progress file when complete
- Use `--continue` flag to resume from previous run

### Error Handling

Errors are handled gracefully:
- Processing continues after individual file failures
- Detailed error report generated: `batch_ingest_errors.json`
- Summary statistics displayed at completion

## Git Integration

When processing files in a git repository, the system automatically:
- Detects the repository root
- Extracts commit SHA and timestamp
- Stores files with temporal versioning
- Tracks file history across commits

## Examples

### Example 1: Ingest Documentation Directory

```bash
# Ingest all markdown files recursively
simics-rag rag ingest-docs-batch ./documentation --pattern "*.md"
```

Output:
```
📁 Directory: ./documentation
🔍 Pattern: *.md
📂 Recursive: Yes
🔄 Force reprocess: No
🧪 Dry run: No
⏯️  Resume: No

🚀 Starting batch ingestion...

============================================================
📊 Batch Ingestion Summary
============================================================
Total files discovered: 25
Files processed: 25
✅ Succeeded: 23
⏭️  Skipped: 0
❌ Failed: 2
⏱️  Total time: 45.32s
📈 Progress: 100.0%

⚠️  2 errors occurred:
  1. ./documentation/empty.md
     - File is empty: ./documentation/empty.md
  2. ./documentation/large.md
     - File exceeds maximum size (50MB): ./documentation/large.md (52.34MB)

📄 Full error report: ./documentation/batch_ingest_errors.json
============================================================

⚠️  Batch ingestion completed with errors
```

### Example 2: Dry Run Validation

```bash
# Validate files without processing
simics-rag rag ingest-docs-batch ./docs --dry-run
```

This validates all files and reports issues without actually ingesting them.

### Example 3: Resume After Interruption

```bash
# Start batch ingestion
simics-rag rag ingest-docs-batch ./large-docs

# If interrupted (Ctrl+C), resume with:
simics-rag rag ingest-docs-batch ./large-docs --continue
```

The system will skip already-processed files and continue from where it left off.

### Example 4: Multiple File Types

```bash
# Ingest multiple documentation formats
simics-rag rag ingest-docs-batch ./docs --pattern "*.md,*.html,*.rst"
```

## Error Report Format

When errors occur, a JSON error report is generated:

```json
{
  "timestamp": "2025-01-15T10:30:00",
  "total_errors": 2,
  "error_summary": {
    "validation": 1,
    "processing": 1
  },
  "errors": [
    {
      "file": "/path/to/empty.md",
      "type": "validation",
      "issues": ["File is empty: /path/to/empty.md"]
    },
    {
      "file": "/path/to/corrupt.md",
      "type": "processing",
      "error": "Failed to parse markdown: Invalid syntax"
    }
  ]
}
```

## Best Practices

1. **Use dry-run first**: Validate files before processing large batches
2. **Monitor progress**: Watch for validation warnings about large files
3. **Check error reports**: Review `batch_ingest_errors.json` for failed files
4. **Use resume capability**: For large batches, use `--continue` if interrupted
5. **Force reprocess carefully**: Use `--force` only when necessary to avoid duplicate processing

## Performance Considerations

- Files are processed sequentially to avoid memory issues
- Large files (>10MB) generate warnings but are still processed
- Files over 50MB are rejected
- Progress is saved after each successful file to enable resume

## Troubleshooting

### Issue: Files not being discovered

**Solution**: Check the pattern and ensure files match. Use `--pattern "*.md,*.html"` for multiple types.

### Issue: Permission denied errors

**Solution**: Ensure you have read permissions for all files in the directory.

### Issue: Progress file not removed

**Solution**: The progress file (`.batch_ingest_progress.json`) is only removed when all files complete successfully. If errors occurred, manually delete it or use `--continue` to resume.

### Issue: Git repository not detected

**Solution**: Ensure you're running the command from within a git repository or a subdirectory of one. The system automatically detects git repositories.

## See Also

- [Temporal Queries](TEMPORAL_QUERIES.md) - Query files at specific points in time
- [Database Backends](DATABASE_BACKENDS.md) - Database schema and backend information
