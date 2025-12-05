# chunk_user_manuals.py - Complete Guide

## Overview
`chunk_user_manuals.py` is a command-line script that processes user manual documents (Markdown/HTML) into RAG-ready chunks with embeddings, summaries, and metadata. It can optionally upload the chunks directly to Supabase.

## Features
- ✅ Process single files or entire directories
- ✅ Generate embeddings using flexible provider system (Qwen/Copilot/OpenAI)
- ✅ Generate summaries for better retrieval
- ✅ Extract rich metadata (headings, code blocks, etc.)
- ✅ Export to JSON and vector DB formats
- ✅ Upload directly to Supabase database
- ✅ Batch processing with retry logic
- ✅ Configurable via environment variables

## Installation

Ensure you have the required dependencies:
```bash
pip install -r requirements.txt
```

## Basic Usage

### Process a Single File
```bash
python3 scripts/chunk_user_manuals.py path/to/document.md
```

### Process a Directory
```bash
python3 scripts/chunk_user_manuals.py docs/ --pattern "*.md" --output-dir ./chunks
```

### Upload to Supabase
```bash
python3 scripts/chunk_user_manuals.py docs/ --upload-to-supabase
```

## Command-Line Options

### Required Arguments
- `input_path` - Path to input file or directory

### Optional Arguments

#### Output Configuration
- `--output-dir, -o` - Output directory for chunks (default: ./manual_chunks)
- `--pattern` - File pattern for directory processing (default: *.md)
- `--no-recursive` - Disable recursive directory search

#### Processing Options
- `--no-embeddings` - Skip embedding generation
- `--no-summaries` - Skip summary generation
- `--dry-run` - Parse and chunk without generating embeddings or summaries

#### Supabase Upload Options
- `--upload-to-supabase` - Upload chunks to Supabase database
- `--skip-delete` - Skip deleting existing records (use upsert instead)
- `--batch-size` - Batch size for Supabase uploads (default: 50)

#### Other Options
- `--verbose, -v` - Enable verbose logging

## Usage Examples

### Example 1: Quick Test (Dry Run)
Process a document without generating embeddings or summaries:
```bash
python3 scripts/chunk_user_manuals.py docs/intro.md --dry-run -v
```

### Example 2: Process with Embeddings
Process a document with embeddings but no summaries:
```bash
python3 scripts/chunk_user_manuals.py docs/intro.md --no-summaries
```

### Example 3: Full Processing
Process with both embeddings and summaries:
```bash
python3 scripts/chunk_user_manuals.py docs/intro.md
```

### Example 4: Process Directory
Process all markdown files in a directory:
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --pattern "*.md" \
  --output-dir ./output/chunks
```

### Example 5: Upload to Supabase
Process and upload to Supabase:
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --upload-to-supabase \
  --batch-size 100
```

### Example 6: Upsert Mode
Upload without deleting existing records:
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --upload-to-supabase \
  --skip-delete
```

### Example 7: Process HTML Files
Process HTML documentation:
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --pattern "*.html" \
  --upload-to-supabase
```

## Configuration

The script uses environment variables from `.env` for configuration:

### Chunking Settings
```bash
MANUAL_MAX_CHUNK_SIZE=1000      # Maximum chunk size
MANUAL_MIN_CHUNK_SIZE=100       # Minimum chunk size
MANUAL_CHUNK_OVERLAP=50         # Overlap between chunks
MANUAL_SIZE_METRIC=characters   # 'characters' or 'tokens'
```

### Model Configuration
```bash
MANUAL_EMBEDDING_MODEL=text-embedding-3-small
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus
```

### Embedding Provider
```bash
USE_QWEN_EMBEDDINGS=false       # Local Qwen model
USE_COPILOT_EMBEDDINGS=true     # GitHub Copilot
# Falls back to OpenAI if both are false
```

### Processing Options
```bash
MANUAL_GENERATE_SUMMARIES=true
MANUAL_GENERATE_EMBEDDINGS=true
USE_CONTEXTUAL_EMBEDDINGS=true
```

### Supabase Configuration
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### Rate Limiting
```bash
COPILOT_REQUESTS_PER_MINUTE=60
```

## Output Files

The script generates two JSON files:

### 1. chunks.json (Standard Format)
Complete output with statistics:
```json
{
  "chunks": [
    {
      "chunk_id": "abc123_0001",
      "content": "Chunk text...",
      "metadata": {
        "source_file": "docs/intro.md",
        "heading_hierarchy": ["Introduction", "Getting Started"],
        "section_level": 2,
        "contains_code": true,
        "code_languages": ["python"],
        "chunk_index": 0,
        "line_start": 1,
        "line_end": 50,
        "char_count": 1000
      },
      "summary": "Summary text...",
      "embedding": [0.1, 0.2, ...]
    }
  ],
  "statistics": {
    "total_documents": 1,
    "total_chunks": 10,
    "total_code_blocks": 3,
    "average_chunk_size": 950.5,
    "processing_time_seconds": 12.34,
    "failed_documents": 0
  }
}
```

### 2. vector_db_chunks.json (Vector DB Format)
Optimized for vector database ingestion:
```json
[
  {
    "id": "abc123_0001",
    "content": "Chunk text...",
    "metadata": { ... },
    "summary": "Summary text...",
    "embedding": [0.1, 0.2, ...]
  }
]
```

## Supabase Upload

When using `--upload-to-supabase`, chunks are uploaded to the `crawled_pages` table with:

### Database Schema
- `url` - Source file path
- `chunk_number` - Chunk index in document
- `content` - Chunk text content
- `metadata` - Full metadata as JSONB
- `source_id` - Extracted from filename
- `content_type` - 'documentation' or 'mixed' (with code)
- `heading_hierarchy` - Array of heading strings
- `embedding` - Vector embedding

### Upload Behavior
- **Default**: Deletes existing records for the same source files before inserting
- **With --skip-delete**: Uses upsert to update existing records or insert new ones
- **Batch Processing**: Uploads in batches (default: 50 records per batch)
- **Retry Logic**: Automatically retries failed batches with exponential backoff
- **Individual Fallback**: If batch fails, tries inserting records individually

## Error Handling

The script includes robust error handling:

### File Errors
- Validates input path exists
- Handles file encoding issues (tries UTF-8, then Latin-1)
- Continues processing on individual file failures

### Processing Errors
- Logs errors for failed documents
- Tracks failed document count in statistics
- Continues processing remaining documents

### Upload Errors
- Retries failed batches up to 3 times
- Falls back to individual inserts if batch fails
- Reports success/failure counts
- Saves local files even if upload fails

## Performance Tips

### 1. Optimize Chunk Size
Larger chunks = fewer API calls but less granular retrieval:
```bash
export MANUAL_MAX_CHUNK_SIZE=1500
export MANUAL_MIN_CHUNK_SIZE=200
```

### 2. Use Local Embeddings
Avoid API rate limits with local Qwen model:
```bash
export USE_QWEN_EMBEDDINGS=true
```

### 3. Disable Summaries for Speed
Skip summary generation for faster processing:
```bash
python3 scripts/chunk_user_manuals.py docs/ --no-summaries
```

### 4. Increase Batch Size
Upload more records per batch (if your database can handle it):
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --upload-to-supabase \
  --batch-size 100
```

### 5. Process in Parallel
Process multiple directories in parallel:
```bash
python3 scripts/chunk_user_manuals.py docs/part1/ --upload-to-supabase &
python3 scripts/chunk_user_manuals.py docs/part2/ --upload-to-supabase &
wait
```

## Troubleshooting

### Issue: "No chunks were generated"
**Cause**: No matching files found or all files failed to process
**Solution**: 
- Check input path exists
- Verify file pattern matches your files
- Use `--verbose` to see detailed errors

### Issue: "Failed to upload to Supabase"
**Cause**: Missing credentials or network issues
**Solution**:
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
- Check network connectivity
- Review error logs with `--verbose`

### Issue: Rate limit errors
**Cause**: Too many API requests
**Solution**:
- Reduce `COPILOT_REQUESTS_PER_MINUTE`
- Use `--no-embeddings` for testing
- Switch to local Qwen embeddings

### Issue: Out of memory
**Cause**: Processing too many large files at once
**Solution**:
- Process files in smaller batches
- Reduce `MANUAL_MAX_CHUNK_SIZE`
- Process directories separately

### Issue: Embeddings not generating
**Cause**: Missing API credentials
**Solution**:
- Set `OPENAI_API_KEY` or `GITHUB_TOKEN` in `.env`
- Or use `USE_QWEN_EMBEDDINGS=true` for local model

## Integration with RAG Pipeline

### Step 1: Process Documentation
```bash
python3 scripts/chunk_user_manuals.py docs/ \
  --upload-to-supabase \
  --pattern "*.md"
```

### Step 2: Query from Application
```python
from src.utils import get_supabase_client, search_documents

client = get_supabase_client()
results = search_documents(
    client=client,
    query="How do I install the software?",
    match_count=5,
    filter_metadata={"content_type": "documentation"}
)
```

### Step 3: Filter by Heading Hierarchy
```python
# Search within specific section
results = search_documents(
    client=client,
    query="configuration options",
    match_count=5,
    filter_metadata={
        "content_type": "documentation",
        "heading_hierarchy": ["User Guide", "Configuration"]
    }
)
```

## Best Practices

1. **Test First**: Use `--dry-run` to verify processing before generating embeddings
2. **Version Control**: Keep output files in version control for reproducibility
3. **Incremental Updates**: Use `--skip-delete` when adding new documents
4. **Monitor Costs**: Track API usage when using Copilot or OpenAI embeddings
5. **Validate Output**: Check `chunks.json` to ensure quality before uploading
6. **Backup Database**: Backup Supabase before bulk uploads
7. **Use Verbose Mode**: Enable `--verbose` when debugging issues

## Advanced Usage

### Custom Configuration
Override environment variables for specific runs:
```bash
MANUAL_MAX_CHUNK_SIZE=2000 \
MANUAL_GENERATE_SUMMARIES=false \
python3 scripts/chunk_user_manuals.py docs/
```

### Process Multiple Formats
Process both Markdown and HTML:
```bash
python3 scripts/chunk_user_manuals.py docs/ --pattern "*.md" --upload-to-supabase
python3 scripts/chunk_user_manuals.py docs/ --pattern "*.html" --upload-to-supabase --skip-delete
```

### Selective Processing
Process only specific subdirectories:
```bash
python3 scripts/chunk_user_manuals.py docs/user-guide/ --upload-to-supabase
python3 scripts/chunk_user_manuals.py docs/api-reference/ --upload-to-supabase --skip-delete
```

## See Also

- `USER_MANUAL_CHUNKER_QUICK_START.md` - Quick start guide for the chunker library
- `CONFIG_ALIGNMENT_SUMMARY.md` - Configuration details
- `EMBEDDING_INTEGRATION_SUMMARY.md` - Embedding system details
- `.env.example` - Example environment configuration
