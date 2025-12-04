# Database Migrations

This directory contains SQL migration scripts for the Supabase database schema.

## Migration 001: Add Documentation Fields

**File:** `001_add_documentation_fields.sql`

**Purpose:** Add support for user manual documentation alongside source code in the RAG system.

### Changes

1. **Added `content_type` field to `crawled_pages` table**
   - Type: `TEXT`
   - Values: `'code'`, `'documentation'`, `'mixed'`
   - Default: `'code'`
   - Purpose: Distinguish between source code, documentation, and mixed content

2. **Added `heading_hierarchy` field to `crawled_pages` table**
   - Type: `JSONB`
   - Default: `'[]'::jsonb`
   - Purpose: Store document structure as hierarchical heading path
   - Example: `["User Guide", "Installation", "Prerequisites"]`

3. **Added `content_type` field to `code_examples` table**
   - Type: `TEXT`
   - Values: `'code'`, `'documentation'`
   - Default: `'code'`
   - Purpose: Distinguish code examples from source vs documentation

4. **Created indexes for efficient querying**
   - `idx_crawled_pages_content_type`: B-tree index on `content_type`
   - `idx_crawled_pages_heading_hierarchy`: GIN index on `heading_hierarchy` for JSONB queries
   - `idx_code_examples_content_type`: B-tree index on `content_type`

5. **Added check constraints**
   - Ensures `content_type` values are valid
   - Prevents invalid data insertion

### Applying the Migration

#### Option 1: Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `001_add_documentation_fields.sql`
4. Paste into the SQL editor
5. Click **Run**

#### Option 2: psql Command Line

```bash
psql $DATABASE_URL < supabase/migrations/001_add_documentation_fields.sql
```

#### Option 3: Supabase CLI

```bash
supabase db push
```

#### Option 4: Python Script

```bash
python scripts/apply_documentation_migration.py
```

Note: The Python script provides instructions but requires manual execution via one of the above methods.

### Verification

After applying the migration, verify the changes:

```sql
-- Check if columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'crawled_pages'
  AND column_name IN ('content_type', 'heading_hierarchy');

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'crawled_pages'
  AND indexname LIKE '%content_type%' OR indexname LIKE '%heading_hierarchy%';

-- Check constraints
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'crawled_pages'::regclass
  AND conname LIKE '%content_type%';
```

### Backward Compatibility

This migration is **backward compatible**:

- Existing records are automatically set to `content_type = 'code'`
- Existing code continues to work without modification
- New fields have sensible defaults
- Indexes are created without locking the table (using `IF NOT EXISTS`)

### Usage Examples

#### Query documentation only

```sql
SELECT * FROM crawled_pages
WHERE content_type = 'documentation'
LIMIT 10;
```

#### Query by heading hierarchy

```sql
-- Find all chunks under "Installation" section
SELECT * FROM crawled_pages
WHERE heading_hierarchy @> '["Installation"]'::jsonb;

-- Find chunks at specific hierarchy level
SELECT * FROM crawled_pages
WHERE jsonb_array_length(heading_hierarchy) = 3;
```

#### Filter mixed content (documentation with code examples)

```sql
SELECT * FROM crawled_pages
WHERE content_type = 'mixed'
  AND metadata->>'contains_code' = 'true';
```

### Integration with UserManualChunker

The `UserManualChunker` pipeline automatically populates these fields:

- `content_type`: Set based on `metadata.contains_code`
  - `'documentation'`: No code blocks
  - `'mixed'`: Contains code examples
- `heading_hierarchy`: Extracted from `metadata.heading_hierarchy`

Example usage:

```python
from src.utils import add_documentation_chunks_to_supabase, get_supabase_client
from user_manual_chunker import UserManualChunker

# Process documentation
chunker = UserManualChunker.from_config(config)
chunks = chunker.process_document("manual.md")

# Convert to dict format
chunk_dicts = [chunk.to_dict() for chunk in chunks]

# Add to database with proper content_type and heading_hierarchy
client = get_supabase_client()
add_documentation_chunks_to_supabase(client, chunk_dicts)
```

### Rollback

If you need to rollback this migration:

```sql
-- Remove indexes
DROP INDEX IF EXISTS idx_crawled_pages_content_type;
DROP INDEX IF EXISTS idx_crawled_pages_heading_hierarchy;
DROP INDEX IF EXISTS idx_code_examples_content_type;

-- Remove constraints
ALTER TABLE crawled_pages DROP CONSTRAINT IF EXISTS check_content_type;
ALTER TABLE code_examples DROP CONSTRAINT IF EXISTS check_code_examples_content_type;

-- Remove columns
ALTER TABLE crawled_pages DROP COLUMN IF EXISTS content_type;
ALTER TABLE crawled_pages DROP COLUMN IF EXISTS heading_hierarchy;
ALTER TABLE code_examples DROP COLUMN IF EXISTS content_type;
```

## Future Migrations

Additional migrations will be numbered sequentially:
- `002_*.sql`
- `003_*.sql`
- etc.

Each migration should include:
- Clear description of changes
- Application instructions
- Verification queries
- Rollback instructions
