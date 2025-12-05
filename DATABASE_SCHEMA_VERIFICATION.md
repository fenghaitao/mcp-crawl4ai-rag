# Database Schema Verification

## Overview
Verification that `add_documentation_chunks_to_supabase()` inserts fields that match the Supabase `crawled_pages` table schema.

## Table Schema (crawled_pages)

### Original Schema (crawled_pages.sql)
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
    unique(url, chunk_number),
    foreign key (source_id) references sources(source_id)
);
```

### Migration Schema (001_add_documentation_fields.sql)
```sql
ALTER TABLE crawled_pages 
ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'code';

ALTER TABLE crawled_pages
ADD COLUMN IF NOT EXISTS heading_hierarchy JSONB DEFAULT '[]'::jsonb;
```

### Complete Schema After Migration
| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | bigserial | NO | auto | Primary key |
| `url` | varchar | NO | - | Source file path |
| `chunk_number` | integer | NO | - | Chunk index |
| `content` | text | NO | - | Chunk text |
| `metadata` | jsonb | NO | '{}' | Full metadata |
| `source_id` | text | NO | - | Source identifier |
| `embedding` | vector(1536) | YES | NULL | Vector embedding |
| `created_at` | timestamp | NO | now() | Auto-generated |
| `content_type` | text | YES | 'code' | Added by migration |
| `heading_hierarchy` | jsonb | YES | '[]' | Added by migration |

## Fields Inserted by add_documentation_chunks_to_supabase()

```python
record = {
    "url": source_file,                              # ✓ Matches
    "chunk_number": metadata.get('chunk_index', 0),  # ✓ Matches
    "content": chunk['content'],                     # ✓ Matches
    "metadata": metadata,                            # ✓ Matches
    "source_id": source_id,                          # ✓ Matches
    "content_type": content_type,                    # ✓ Matches (from migration)
    "heading_hierarchy": metadata.get('heading_hierarchy', []),  # ✓ Matches (from migration)
    "embedding": chunk.get('embedding')              # ✓ Matches
}
```

## Field-by-Field Verification

### ✅ url
- **Database**: `varchar not null`
- **Inserted**: `source_file` (string from metadata)
- **Status**: ✓ MATCH

### ✅ chunk_number
- **Database**: `integer not null`
- **Inserted**: `metadata.get('chunk_index', 0)` (integer)
- **Status**: ✓ MATCH

### ✅ content
- **Database**: `text not null`
- **Inserted**: `chunk['content']` (string)
- **Status**: ✓ MATCH

### ✅ metadata
- **Database**: `jsonb not null default '{}'::jsonb`
- **Inserted**: `metadata` (dict/JSONB)
- **Status**: ✓ MATCH

### ✅ source_id
- **Database**: `text not null`
- **Inserted**: `Path(source_file).stem` (string)
- **Status**: ✓ MATCH
- **Note**: Must exist in `sources` table (foreign key constraint)

### ✅ embedding
- **Database**: `vector(1536)` (nullable)
- **Inserted**: `chunk.get('embedding')` (list of floats or None)
- **Status**: ✓ MATCH

### ✅ content_type
- **Database**: `text` (nullable, default 'code')
- **Inserted**: `'documentation'` or `'mixed'` (string)
- **Status**: ✓ MATCH (added by migration)
- **Constraint**: Must be in ('code', 'documentation', 'mixed')

### ✅ heading_hierarchy
- **Database**: `jsonb` (nullable, default '[]')
- **Inserted**: `metadata.get('heading_hierarchy', [])` (list)
- **Status**: ✓ MATCH (added by migration)

### ⚠️ id (Auto-generated)
- **Database**: `bigserial primary key`
- **Inserted**: Not provided (auto-generated)
- **Status**: ✓ CORRECT (should not be provided)

### ⚠️ created_at (Auto-generated)
- **Database**: `timestamp with time zone default now()`
- **Inserted**: Not provided (auto-generated)
- **Status**: ✓ CORRECT (should not be provided)

## Constraints Verification

### Unique Constraint
```sql
unique(url, chunk_number)
```
- **Status**: ✓ HANDLED
- The function uses `on_conflict="url,chunk_number"` for upsert mode
- In delete mode, existing records are deleted first

### Foreign Key Constraint
```sql
foreign key (source_id) references sources(source_id)
```
- **Status**: ⚠️ REQUIRES ATTENTION
- The `source_id` must exist in the `sources` table
- Current implementation: Uses `Path(source_file).stem` as source_id
- **Recommendation**: Ensure source_id exists in sources table before inserting

### Check Constraint (content_type)
```sql
CHECK (content_type IN ('code', 'documentation', 'mixed'))
```
- **Status**: ✓ SATISFIED
- Function only inserts 'documentation' or 'mixed'
- Both values are valid per constraint

## Potential Issues

### 1. Source ID Foreign Key ⚠️

**Issue**: The function generates `source_id` from filename, but this may not exist in `sources` table.

**Current Code**:
```python
source_id = Path(source_file).stem if source_file else 'unknown'
```

**Example**:
- File: `docs/user-guide/installation.md`
- Generated source_id: `installation`
- This may not exist in `sources` table!

**Solutions**:

#### Option A: Use a default source_id
```python
# Use a generic source_id for all documentation
source_id = 'user-documentation'
```

Then ensure this exists in sources table:
```sql
INSERT INTO sources (source_id, summary, total_word_count) VALUES
    ('user-documentation', 'User manual documentation', 0)
ON CONFLICT (source_id) DO NOTHING;
```

#### Option B: Extract from directory structure
```python
# Extract from path: docs/simics-guide/file.md -> simics-guide
from pathlib import Path
path_parts = Path(source_file).parts
if len(path_parts) > 1:
    source_id = path_parts[-2]  # Parent directory
else:
    source_id = 'user-documentation'
```

#### Option C: Add to metadata and use that
```python
# Use source_id from metadata if provided
source_id = metadata.get('source_id', 'user-documentation')
```

### 2. Embedding Dimension

**Issue**: Embeddings must be exactly 1536 dimensions.

**Current Code**:
```python
"embedding": chunk.get('embedding')
```

**Verification Needed**: Ensure embeddings from `EmbeddingGenerator` are 1536 dimensions.

**Status**: ✓ CORRECT - `text-embedding-3-small` produces 1536-dimensional embeddings

## Recommendations

### 1. Fix source_id Generation

Update `add_documentation_chunks_to_supabase()` to use a consistent source_id:

```python
# Option 1: Use a default source_id
source_id = metadata.get('source_id', 'user-documentation')

# Option 2: Extract from path
from pathlib import Path
path = Path(source_file)
if len(path.parts) > 1:
    # Use parent directory as source_id
    source_id = path.parts[-2]
else:
    source_id = 'user-documentation'
```

### 2. Ensure Source Exists

Before running the script, ensure the source exists:

```sql
INSERT INTO sources (source_id, summary, total_word_count) VALUES
    ('user-documentation', 'User manual and documentation files', 0)
ON CONFLICT (source_id) DO NOTHING;
```

Or add this to the script:
```python
# Ensure source exists
try:
    client.table('sources').upsert({
        'source_id': source_id,
        'summary': f'Documentation from {source_file}',
        'total_word_count': 0
    }, on_conflict='source_id').execute()
except Exception as e:
    print(f"Warning: Could not create source {source_id}: {e}")
```

### 3. Add Validation

Add validation before insertion:

```python
# Validate embedding dimension
if chunk.get('embedding') is not None:
    embedding = chunk['embedding']
    if isinstance(embedding, list) and len(embedding) != 1536:
        print(f"Warning: Embedding has {len(embedding)} dimensions, expected 1536")
        embedding = None
```

## Summary

### ✅ All Required Fields Match
All fields inserted by `add_documentation_chunks_to_supabase()` match the database schema after applying the migration.

### ⚠️ Action Required
1. **Apply Migration**: Ensure `001_add_documentation_fields.sql` is applied to database
2. **Fix source_id**: Update function to use consistent source_id strategy
3. **Create Source**: Ensure source_id exists in sources table before inserting

### ✓ Schema Compatibility
The function is compatible with the database schema, but requires:
- Migration `001_add_documentation_fields.sql` applied
- Source record exists in `sources` table
- Proper source_id generation strategy
