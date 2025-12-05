# Database Schema Fix Summary

## Issue Identified

The `add_documentation_chunks_to_supabase()` function was inserting fields (`content_type` and `heading_hierarchy`) that don't exist in the original `crawled_pages` table schema, and was generating `source_id` values that may not exist in the `sources` table.

## Root Cause

1. **Missing Columns**: The original `crawled_pages.sql` doesn't include `content_type` and `heading_hierarchy` columns
2. **Migration Required**: These columns are added by migration `001_add_documentation_fields.sql`
3. **Foreign Key Issue**: Generated `source_id` from filename may not exist in `sources` table

## Fixes Applied

### 1. Fixed source_id Generation

**Before**:
```python
source_id = Path(source_file).stem if source_file else 'unknown'
```
This would generate source_id like `installation` from `docs/installation.md`, which doesn't exist in sources table.

**After**:
```python
if 'source_id' in metadata:
    source_id = metadata['source_id']
else:
    # Use 'user-documentation' as default for all user manual chunks
    source_id = 'user-documentation'
```
Now uses a consistent `user-documentation` source_id for all user manual chunks.

### 2. Created Migration for user-documentation Source

Created `supabase/migrations/002_add_user_documentation_source.sql`:
```sql
INSERT INTO sources (source_id, summary, total_word_count) VALUES
    ('user-documentation', 'User manual and technical documentation files', 0)
ON CONFLICT (source_id) DO NOTHING;
```

### 3. Created Migration Application Script

Created `scripts/apply_all_migrations.py` to help apply migrations.

## Required Migrations

### Migration 1: Add Documentation Fields
**File**: `supabase/migrations/001_add_documentation_fields.sql`

**Purpose**: Adds `content_type` and `heading_hierarchy` columns to `crawled_pages` table

**SQL**:
```sql
ALTER TABLE crawled_pages 
ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'code';

ALTER TABLE crawled_pages
ADD COLUMN IF NOT EXISTS heading_hierarchy JSONB DEFAULT '[]'::jsonb;

-- Indexes and constraints...
```

### Migration 2: Add user-documentation Source
**File**: `supabase/migrations/002_add_user_documentation_source.sql`

**Purpose**: Ensures `user-documentation` source exists in `sources` table

**SQL**:
```sql
INSERT INTO sources (source_id, summary, total_word_count) VALUES
    ('user-documentation', 'User manual and technical documentation files', 0)
ON CONFLICT (source_id) DO NOTHING;
```

## How to Apply Migrations

### Option 1: Supabase Dashboard (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Navigate to **SQL Editor**
4. Copy and paste `supabase/migrations/001_add_documentation_fields.sql`
5. Click **Run**
6. Repeat for `supabase/migrations/002_add_user_documentation_source.sql`

### Option 2: Using psql

```bash
# Get your connection string from Supabase dashboard
psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" \
  -f supabase/migrations/001_add_documentation_fields.sql

psql "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres" \
  -f supabase/migrations/002_add_user_documentation_source.sql
```

### Option 3: Using apply_documentation_migration.py

```bash
python3 scripts/apply_documentation_migration.py
```

## Verification

After applying migrations, verify the schema:

### Check Columns
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'crawled_pages'
ORDER BY ordinal_position;
```

Expected output should include:
- `content_type` (text, nullable, default 'code')
- `heading_hierarchy` (jsonb, nullable, default '[]')

### Check Sources
```sql
SELECT source_id, summary FROM sources;
```

Expected output should include:
- `user-documentation` | User manual and technical documentation files

### Check Constraints
```sql
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'crawled_pages';
```

Should include:
- `check_content_type` (CHECK constraint)

## Complete Schema After Migrations

```sql
create table crawled_pages (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    source_id text not null,
    embedding vector(1536),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    content_type text default 'code',                    -- Added by migration 001
    heading_hierarchy jsonb default '[]'::jsonb,         -- Added by migration 001
    
    unique(url, chunk_number),
    foreign key (source_id) references sources(source_id),
    check (content_type IN ('code', 'documentation', 'mixed'))  -- Added by migration 001
);
```

## Field Mapping Verification

| Function Field | Database Column | Type | Status |
|---------------|-----------------|------|--------|
| `url` | `url` | varchar | ✓ Match |
| `chunk_number` | `chunk_number` | integer | ✓ Match |
| `content` | `content` | text | ✓ Match |
| `metadata` | `metadata` | jsonb | ✓ Match |
| `source_id` | `source_id` | text | ✓ Fixed |
| `embedding` | `embedding` | vector(1536) | ✓ Match |
| `content_type` | `content_type` | text | ✓ Match (requires migration 001) |
| `heading_hierarchy` | `heading_hierarchy` | jsonb | ✓ Match (requires migration 001) |

## Testing

### Test 1: Verify Migrations Applied
```bash
python3 scripts/apply_all_migrations.py
```

### Test 2: Test Upload Without Migrations
```bash
# This should fail with "column does not exist" error
python3 scripts/chunk_user_manuals.py docs/test.md --upload-to-supabase
```

### Test 3: Test Upload With Migrations
```bash
# After applying migrations, this should succeed
python3 scripts/chunk_user_manuals.py docs/test.md --upload-to-supabase
```

### Test 4: Verify Data in Database
```sql
SELECT 
    url, 
    chunk_number, 
    source_id, 
    content_type, 
    heading_hierarchy,
    length(content) as content_length
FROM crawled_pages
WHERE source_id = 'user-documentation'
LIMIT 5;
```

## Files Modified

1. `src/utils.py` - Fixed source_id generation in `add_documentation_chunks_to_supabase()`

## Files Created

1. `supabase/migrations/002_add_user_documentation_source.sql` - Adds user-documentation source
2. `scripts/apply_all_migrations.py` - Helper script for migration application
3. `DATABASE_SCHEMA_VERIFICATION.md` - Detailed schema verification
4. `DATABASE_SCHEMA_FIX_SUMMARY.md` - This summary

## Next Steps

1. **Apply Migrations**: Use Supabase Dashboard SQL Editor to apply both migrations
2. **Verify Schema**: Run verification queries to ensure columns exist
3. **Test Upload**: Run `chunk_user_manuals.py` with `--upload-to-supabase` flag
4. **Monitor**: Check Supabase logs for any errors during upload

## Troubleshooting

### Error: "column 'content_type' does not exist"
**Solution**: Apply migration `001_add_documentation_fields.sql`

### Error: "column 'heading_hierarchy' does not exist"
**Solution**: Apply migration `001_add_documentation_fields.sql`

### Error: "foreign key constraint violation on source_id"
**Solution**: Apply migration `002_add_user_documentation_source.sql`

### Error: "check constraint violation on content_type"
**Solution**: Ensure content_type is one of: 'code', 'documentation', 'mixed'

## Summary

✅ **Fixed**: source_id generation now uses consistent 'user-documentation' value
✅ **Created**: Migration to add user-documentation source
✅ **Verified**: All fields match database schema after migrations
✅ **Documented**: Complete schema verification and migration guide

The `add_documentation_chunks_to_supabase()` function is now fully compatible with the database schema, provided the migrations are applied.
