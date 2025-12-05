# chunk_user_manuals.py Extension Summary

## Overview
Extended `scripts/chunk_user_manuals.py` to support direct upload to Supabase database after processing documents.

## Changes Made

### 1. Added Imports
```python
from utils import get_supabase_client, add_documentation_chunks_to_supabase
```

### 2. Added Command-Line Arguments
- `--upload-to-supabase` - Enable upload to Supabase
- `--skip-delete` - Use upsert instead of delete+insert
- `--batch-size` - Configure batch size (default: 50)

### 3. Added Upload Logic
After processing and exporting chunks:
1. Connects to Supabase using credentials from `.env`
2. Converts `ProcessedChunk` objects to dictionaries
3. Calls `add_documentation_chunks_to_supabase()` with proper parameters
4. Handles errors gracefully (saves local files even if upload fails)

## Usage Examples

### Basic Upload
```bash
python3 scripts/chunk_user_manuals.py docs/ --upload-to-supabase
```

### Upload with Upsert
```bash
python3 scripts/chunk_user_manuals.py docs/ --upload-to-supabase --skip-delete
```

### Custom Batch Size
```bash
python3 scripts/chunk_user_manuals.py docs/ --upload-to-supabase --batch-size 100
```

### Dry Run (No Upload)
```bash
python3 scripts/chunk_user_manuals.py docs/ --dry-run
```

## Data Flow

```
Input Documents
    ↓
UserManualChunker.process_document()
    ↓
ProcessedChunk objects (with embeddings & metadata)
    ↓
Convert to dictionaries via to_dict()
    ↓
add_documentation_chunks_to_supabase()
    ↓
Supabase crawled_pages table
```

## Database Schema Mapping

### ProcessedChunk → crawled_pages

| ProcessedChunk Field | Database Column | Notes |
|---------------------|-----------------|-------|
| `chunk_id` | Not stored directly | Used for local tracking |
| `content` | `content` | Chunk text content |
| `metadata.source_file` | `url` | Source file path |
| `metadata.chunk_index` | `chunk_number` | Position in document |
| `metadata` (full object) | `metadata` | JSONB column |
| `metadata.source_file` (stem) | `source_id` | Filename without extension |
| `metadata.contains_code` | `content_type` | 'documentation' or 'mixed' |
| `metadata.heading_hierarchy` | `heading_hierarchy` | Array of heading strings |
| `embedding` | `embedding` | Vector embedding |
| `summary` | Not stored | Could be added to metadata |

### Content Type Logic
```python
if metadata.get('contains_code', False):
    content_type = 'mixed'  # Documentation with code examples
else:
    content_type = 'documentation'  # Pure documentation
```

## Features

### ✅ Batch Processing
- Uploads in configurable batches (default: 50)
- Reduces database load
- Improves performance

### ✅ Retry Logic
- Retries failed batches up to 3 times
- Exponential backoff (1s, 2s, 4s)
- Falls back to individual inserts if batch fails

### ✅ Delete vs Upsert
- **Default**: Deletes existing records for same source files
- **With --skip-delete**: Uses upsert (on_conflict="url,chunk_number")

### ✅ Error Handling
- Graceful error handling
- Continues processing on failures
- Reports success/failure counts
- Saves local files even if upload fails

### ✅ Progress Reporting
- Logs connection status
- Reports upload progress
- Shows batch completion
- Displays final statistics

## Testing

### Test Without Upload
```bash
python3 scripts/chunk_user_manuals.py dmr_1_4/introduction.md --dry-run -v
```

### Test With Upload (Requires Supabase Credentials)
```bash
python3 scripts/chunk_user_manuals.py dmr_1_4/introduction.md \
  --upload-to-supabase \
  --batch-size 10 \
  -v
```

## Environment Variables Required

For Supabase upload to work, these must be set in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

## Benefits

1. **Streamlined Workflow**: Process and upload in one command
2. **Consistent Data**: Uses same upload function as other scripts
3. **Flexible Options**: Can skip upload, use upsert, or customize batch size
4. **Robust**: Handles errors gracefully with retry logic
5. **Transparent**: Detailed logging shows exactly what's happening
6. **Safe**: Saves local files even if upload fails

## Integration with Existing Scripts

The script now fits into the complete pipeline:

```bash
# Step 1: Download pages
python3 scripts/download_pages_locally.py

# Step 2: Chunk and upload user manuals
python3 scripts/chunk_user_manuals.py pipeline_output/downloaded_pages/ \
  --upload-to-supabase \
  --pattern "*.md"

# Step 3: Process source code (if needed)
python3 scripts/crawl_simics_source.py --upload
```

## Files Modified

1. `scripts/chunk_user_manuals.py` - Added upload functionality

## Documentation Created

1. `CHUNK_USER_MANUALS_GUIDE.md` - Complete usage guide
2. `CHUNK_USER_MANUALS_SUMMARY.md` - This summary

## Next Steps

The script is ready for production use:
- Process documentation with `--upload-to-supabase`
- Use `--skip-delete` for incremental updates
- Adjust `--batch-size` based on your database performance
- Monitor upload progress with `--verbose`
