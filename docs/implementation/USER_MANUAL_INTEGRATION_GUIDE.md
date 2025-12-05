# User Manual Integration Guide

This guide explains how the user manual chunking system integrates with the existing RAG pipeline.

## Overview

The user manual chunking system has been integrated into the existing crawl pipeline to process technical documentation alongside source code. The integration includes:

1. **Pipeline Integration**: Added `--process-manuals` flag to `crawl_pipeline.py`
2. **Documentation Summarization**: Extended `code_summarizer.py` with documentation-specific prompts
3. **Database Schema**: Added fields to distinguish documentation from code and enable hierarchical retrieval

## Components

### 1. Pipeline Integration

#### crawl_pipeline.py

Added a new step to process user manuals after local file crawling:

```bash
# Process with manual chunking enabled
python scripts/crawl_pipeline.py \
  --mode site \
  https://example.com/docs \
  --process-manuals
```

**New Flag:**
- `--process-manuals`: Enable user manual processing after local file crawling

**Workflow:**
1. Extract URLs from site
2. Download pages locally
3. Crawl local files (existing step)
4. **NEW:** Process user manuals (if `--process-manuals` is set)
5. Crawl Simics source (if enabled)

#### chunk_user_manuals.py

New standalone script for processing user manuals:

```bash
# Process a single file
python scripts/chunk_user_manuals.py manual.md

# Process a directory
python scripts/chunk_user_manuals.py docs/ --pattern "*.md"

# Dry run (no embeddings/summaries)
python scripts/chunk_user_manuals.py docs/ --dry-run

# Custom output directory
python scripts/chunk_user_manuals.py docs/ --output-dir ./output
```

**Options:**
- `input_path`: File or directory to process
- `--output-dir, -o`: Output directory (default: `./manual_chunks`)
- `--pattern`: File pattern for directory processing (default: `*.md`)
- `--no-recursive`: Disable recursive directory search
- `--no-embeddings`: Skip embedding generation
- `--no-summaries`: Skip summary generation
- `--dry-run`: Parse and chunk only
- `--verbose, -v`: Enable verbose logging

**Output:**
- `chunks.json`: Standard format with statistics
- `vector_db_chunks.json`: Vector database format

### 2. Documentation Summarization

#### code_summarizer.py

Added `generate_documentation_summary()` function for documentation-specific summarization:

```python
from src.code_summarizer import generate_documentation_summary

summary = generate_documentation_summary(
    chunk=document_chunk,
    doc_context="Simics DML Reference Manual",
    metadata=chunk_metadata,
    model="iflow/qwen3-coder-plus",
    max_tokens=150
)
```

**Features:**
- Documentation-specific prompts (vs code-specific prompts)
- Mentions code examples when present
- Fallback to extractive summaries on failure
- Integrates with existing iflow_client

**Integration with SummaryGenerator:**

The `SummaryGenerator` class now uses `generate_documentation_summary()` automatically:

```python
from user_manual_chunker import SummaryGenerator

generator = SummaryGenerator(
    model="iflow/qwen3-coder-plus",
    max_summary_length=150
)

summary = generator.generate_summary(chunk, doc_context, metadata)
# Internally calls generate_documentation_summary()
```

### 3. Database Schema

#### New Fields

**crawled_pages table:**
- `content_type` (TEXT): `'code'`, `'documentation'`, or `'mixed'`
- `heading_hierarchy` (JSONB): Hierarchical heading path as JSON array

**code_examples table:**
- `content_type` (TEXT): `'code'` or `'documentation'`

#### Indexes

- `idx_crawled_pages_content_type`: B-tree index for filtering by content type
- `idx_crawled_pages_heading_hierarchy`: GIN index for JSONB queries
- `idx_code_examples_content_type`: B-tree index for code examples

#### Migration

Apply the database migration:

```bash
# Option 1: Via Supabase Dashboard
# Copy contents of supabase/migrations/001_add_documentation_fields.sql
# Paste into SQL Editor and run

# Option 2: Via psql
psql $DATABASE_URL < supabase/migrations/001_add_documentation_fields.sql

# Option 3: Via Supabase CLI
supabase db push

# Option 4: Python script (provides instructions)
python scripts/apply_documentation_migration.py
```

See `supabase/migrations/README.md` for detailed migration instructions.

#### Database Helper Function

New function in `src/utils.py`:

```python
from src.utils import add_documentation_chunks_to_supabase, get_supabase_client

# Process documentation
chunks = chunker.process_document("manual.md")
chunk_dicts = [chunk.to_dict() for chunk in chunks]

# Add to database
client = get_supabase_client()
add_documentation_chunks_to_supabase(client, chunk_dicts)
```

**Features:**
- Automatically sets `content_type` based on code presence
- Extracts `heading_hierarchy` from metadata
- Batch insertion with retry logic
- Handles errors gracefully

## Usage Examples

### Example 1: Process Documentation in Pipeline

```bash
# Full pipeline with manual processing
python scripts/crawl_pipeline.py \
  --mode site \
  https://intel.github.io/simics/docs/dml-1.4-reference-manual/ \
  --process-manuals \
  --output-dir ./pipeline_output
```

This will:
1. Extract URLs from the site
2. Download pages locally to `pipeline_output/downloaded_pages/`
3. Crawl and store in database
4. Process manuals and store chunks in `pipeline_output/manual_chunks/`

### Example 2: Process Existing Downloaded Files

```bash
# Process already-downloaded markdown files
python scripts/chunk_user_manuals.py \
  pipeline_output/downloaded_pages/ \
  --pattern "*.md" \
  --output-dir ./manual_chunks
```

### Example 3: Programmatic Usage

```python
from user_manual_chunker import UserManualChunker
from user_manual_chunker.config import ChunkerConfig
from src.utils import add_documentation_chunks_to_supabase, get_supabase_client

# Configure chunker
config = ChunkerConfig.from_env()
config.generate_embeddings = True
config.generate_summaries = True

# Create chunker
chunker = UserManualChunker.from_config(config)

# Process document
chunks = chunker.process_document("manual.md")

# Convert to dict format
chunk_dicts = [chunk.to_dict() for chunk in chunks]

# Add to database
client = get_supabase_client()
add_documentation_chunks_to_supabase(client, chunk_dicts)

# Get statistics
stats = chunker.get_statistics()
print(f"Processed {stats['total_chunks']} chunks")
```

### Example 4: Query Documentation

```python
from src.utils import get_supabase_client

client = get_supabase_client()

# Query documentation only
result = client.table("crawled_pages") \
    .select("*") \
    .eq("content_type", "documentation") \
    .limit(10) \
    .execute()

# Query by heading hierarchy
result = client.table("crawled_pages") \
    .select("*") \
    .filter("heading_hierarchy", "cs", '["Installation"]') \
    .execute()

# Query mixed content (documentation with code)
result = client.table("crawled_pages") \
    .select("*") \
    .eq("content_type", "mixed") \
    .execute()
```

## Configuration

### Environment Variables

The user manual chunker respects these environment variables:

```bash
# Chunking configuration
MANUAL_MAX_CHUNK_SIZE=1000
MANUAL_MIN_CHUNK_SIZE=100
MANUAL_CHUNK_OVERLAP=50
MANUAL_SIZE_METRIC=characters  # or tokens

# Embedding configuration
MANUAL_EMBEDDING_MODEL=text-embedding-3-small
MANUAL_GENERATE_EMBEDDINGS=true

# Summary configuration
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus
MANUAL_GENERATE_SUMMARIES=true
MANUAL_MAX_SUMMARY_LENGTH=150
MANUAL_SUMMARY_TIMEOUT_SECONDS=30

# Batch processing
MANUAL_EMBEDDING_BATCH_SIZE=32
```

Add these to your `.env` file or set them in your environment.

## Architecture

### Data Flow

```
Input Document (MD/HTML)
    ↓
MarkdownParser / HTMLParser
    ↓
DocumentStructure
    ↓
SemanticChunker
    ↓
DocumentChunk[]
    ↓
MetadataExtractor → ChunkMetadata
    ↓
SummaryGenerator → Summary (via code_summarizer)
    ↓
EmbeddingGenerator → Embedding
    ↓
ProcessedChunk[]
    ↓
add_documentation_chunks_to_supabase()
    ↓
Supabase Database
```

### Integration Points

1. **crawl_pipeline.py** → **chunk_user_manuals.py**
   - Pipeline calls script after local file crawling
   - Passes downloaded pages directory

2. **SummaryGenerator** → **code_summarizer.generate_documentation_summary()**
   - Summary generator uses documentation-specific prompts
   - Fallback to local implementation if import fails

3. **UserManualChunker** → **add_documentation_chunks_to_supabase()**
   - Chunker outputs ProcessedChunk objects
   - Helper function converts and stores in database

## Backward Compatibility

The integration is fully backward compatible:

- Existing code continues to work without modification
- New fields have sensible defaults (`content_type='code'`)
- Database migration is non-breaking
- New functionality is opt-in via `--process-manuals` flag

## Testing

### Test Pipeline Integration

```bash
# Test with dry run
python scripts/crawl_pipeline.py \
  --mode single \
  https://example.com/page.html \
  --process-manuals \
  --skip-crawl
```

### Test Manual Processing

```bash
# Test with a single file
python scripts/chunk_user_manuals.py \
  pipeline_output/downloaded_pages/simics_docs_dml-1.4-reference-manual_language.md \
  --dry-run \
  --verbose
```

### Test Database Integration

```python
# Test database helper
from src.utils import add_documentation_chunks_to_supabase, get_supabase_client

# Create test chunk
test_chunk = {
    'chunk_id': 'test_001',
    'content': 'Test content',
    'metadata': {
        'source_file': 'test.md',
        'heading_hierarchy': ['Test', 'Section'],
        'section_level': 2,
        'contains_code': False,
        'code_languages': [],
        'chunk_index': 0,
        'line_start': 1,
        'line_end': 10,
        'char_count': 100
    },
    'summary': 'Test summary',
    'embedding': [0.1] * 1536
}

client = get_supabase_client()
add_documentation_chunks_to_supabase(client, [test_chunk])
```

## Troubleshooting

### Issue: Migration not applied

**Solution:** Apply the migration manually via Supabase Dashboard or psql:
```bash
psql $DATABASE_URL < supabase/migrations/001_add_documentation_fields.sql
```

### Issue: Import errors

**Solution:** Ensure you're running from the project root:
```bash
cd /path/to/mcp-crawl4ai-rag
python scripts/chunk_user_manuals.py ...
```

### Issue: Embedding generation fails

**Solution:** Check your API keys and configuration:
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $MANUAL_EMBEDDING_MODEL

# Test with dry run
python scripts/chunk_user_manuals.py docs/ --dry-run
```

### Issue: Summary generation times out

**Solution:** Increase timeout or disable summaries:
```bash
# Increase timeout
export MANUAL_SUMMARY_TIMEOUT_SECONDS=60

# Or disable summaries
python scripts/chunk_user_manuals.py docs/ --no-summaries
```

## Next Steps

1. **Apply Database Migration**: Follow instructions in `supabase/migrations/README.md`
2. **Configure Environment**: Set environment variables in `.env`
3. **Test Integration**: Run pipeline with `--process-manuals` flag
4. **Query Documentation**: Use new `content_type` and `heading_hierarchy` fields

## References

- **Requirements**: `.kiro/specs/user-manual-rag/requirements.md`
- **Design**: `.kiro/specs/user-manual-rag/design.md`
- **Tasks**: `.kiro/specs/user-manual-rag/tasks.md`
- **Migration Guide**: `supabase/migrations/README.md`
- **Pipeline Script**: `scripts/crawl_pipeline.py`
- **Chunking Script**: `scripts/chunk_user_manuals.py`
- **Database Schema**: `supabase/migrations/001_add_documentation_fields.sql`
