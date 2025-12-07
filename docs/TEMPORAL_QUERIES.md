# Temporal Queries Guide

This guide explains how to query files at specific points in time using the temporal versioning system.

## Overview

The temporal query system allows you to:
- Query current versions of files
- Query files at specific timestamps
- Query files at specific git commits
- View complete file history
- Track documentation evolution over time

## Temporal Versioning Model

Each file version is tracked with:
- **valid_from**: When this version became valid (git commit timestamp)
- **valid_until**: When superseded by newer version (NULL if current)
- **commit_sha**: Git commit that introduced this version
- **repo_id**: Repository containing the file

## Query Commands

### Query Current File

Get the currently valid version of a file:

```bash
simics-rag rag query-file <repo-url> <file-path>
```

Example:
```bash
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md
```

Output:
```
============================================================
📄 File Information
============================================================
File ID: 42
Repository: https://github.com/user/repo.git
File Path: docs/guide.md
Commit SHA: abc123def456
Content Hash: 7f8a9b2c3d4e...
File Size: 15234 bytes
Word Count: 2456
Chunk Count: 12
Content Type: documentation
Valid From: 2025-01-15 10:30:00
Valid Until: Current
Ingested At: 2025-01-15 10:35:00
============================================================
```

### Query File at Specific Commit

Get the version of a file from a specific git commit:

```bash
simics-rag rag query-file <repo-url> <file-path> --commit <commit-sha>
```

Example:
```bash
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --commit abc123
```

### Query File at Specific Time

Get the version of a file that was valid at a specific timestamp:

```bash
simics-rag rag query-file <repo-url> <file-path> --timestamp <iso-timestamp>
```

Example:
```bash
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --timestamp 2025-01-10T14:30:00
```

### View File History

See all versions of a file ordered by time:

```bash
simics-rag rag file-history <repo-url> <file-path>
```

Example:
```bash
simics-rag rag file-history https://github.com/user/repo.git docs/guide.md
```

Output:
```
====================================================================================================
📜 File History: docs/guide.md
📦 Repository: https://github.com/user/repo.git
📊 Total versions: 3
====================================================================================================
Commit       Valid From           Valid Until          Words      Chunks  
----------------------------------------------------------------------------------------------------
ghi789       2025-01-15 10:30:00  Current              2456       12      
def456       2025-01-10 14:20:00  2025-01-15 10:30:00  2103       10      
abc123       2025-01-05 09:15:00  2025-01-10 14:20:00  1847       9       
====================================================================================================
```

### List Files

List all ingested files with filtering:

```bash
# List all current files
simics-rag rag list-files

# Filter by repository
simics-rag rag list-files --repo-url https://github.com/user/repo.git

# Filter by content type
simics-rag rag list-files --content-type documentation

# Show all versions (not just current)
simics-rag rag list-files --all-versions

# Pagination
simics-rag rag list-files --limit 50 --offset 100
```

### List Chunks

View all chunks for a specific file:

```bash
simics-rag rag list-chunks <file-id>
```

Example:
```bash
simics-rag rag list-chunks 42
```

## JSON Output

All query commands support JSON output for programmatic use:

```bash
# Query file with JSON output
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --json

# File history with JSON output
simics-rag rag file-history https://github.com/user/repo.git docs/guide.md --json

# List files with JSON output
simics-rag rag list-files --json
```

Example JSON output:
```json
{
  "file_id": 42,
  "repo_url": "https://github.com/user/repo.git",
  "file_path": "docs/guide.md",
  "commit_sha": "abc123def456",
  "content_hash": "7f8a9b2c3d4e5f6a7b8c9d0e1f2a3b4c",
  "file_size": 15234,
  "word_count": 2456,
  "chunk_count": 12,
  "content_type": "documentation",
  "valid_from": "2025-01-15T10:30:00",
  "valid_until": null,
  "ingested_at": "2025-01-15T10:35:00"
}
```

## Use Cases

### Use Case 1: Track Documentation Changes

View how a specific document evolved over time:

```bash
# Get complete history
simics-rag rag file-history https://github.com/user/repo.git docs/api.md

# Compare versions by querying at different commits
simics-rag rag query-file https://github.com/user/repo.git docs/api.md --commit old-commit
simics-rag rag query-file https://github.com/user/repo.git docs/api.md --commit new-commit
```

### Use Case 2: Point-in-Time Recovery

Retrieve documentation as it existed at a specific date:

```bash
# Get all files as they were on a specific date
simics-rag rag list-files --all-versions | grep "2025-01-10"

# Query specific file at that time
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --timestamp 2025-01-10T00:00:00
```

### Use Case 3: Audit Trail

Track when documentation was updated:

```bash
# View complete history with timestamps
simics-rag rag file-history https://github.com/user/repo.git docs/guide.md --json
```

### Use Case 4: Version Comparison

Compare different versions of a file:

```bash
# Get version from commit A
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --commit abc123 --json > version-a.json

# Get version from commit B
simics-rag rag query-file https://github.com/user/repo.git docs/guide.md --commit def456 --json > version-b.json

# Compare the JSON files
diff version-a.json version-b.json
```

## Temporal Query Semantics

### Current Version Query

Returns the file version where `valid_until IS NULL`:

```sql
SELECT * FROM files 
WHERE repo_id = ? AND file_path = ? AND valid_until IS NULL;
```

### Point-in-Time Query

Returns the file version valid at a specific timestamp:

```sql
SELECT * FROM files
WHERE repo_id = ? AND file_path = ?
  AND valid_from <= ? AND (valid_until IS NULL OR valid_until > ?)
ORDER BY valid_from DESC
LIMIT 1;
```

### Commit Query

Returns the file version from a specific commit:

```sql
SELECT * FROM files
WHERE repo_id = ? AND file_path = ? AND commit_sha = ?;
```

### History Query

Returns all versions ordered by time:

```sql
SELECT * FROM files
WHERE repo_id = ? AND file_path = ?
ORDER BY valid_from DESC;
```

## Best Practices

1. **Use current queries by default**: Most use cases need the current version
2. **Specify timestamps in ISO format**: Use `YYYY-MM-DDTHH:MM:SS` format
3. **Use JSON output for automation**: Parse JSON for programmatic access
4. **Check file history before temporal queries**: Verify versions exist at desired times
5. **Use commit SHAs for reproducibility**: Commits are immutable, timestamps may vary

## Limitations

- Temporal queries only work for files in git repositories
- Files outside git repos don't have temporal versioning
- Timestamps are based on git commit times, not file modification times
- History is limited to ingested versions (not all git history)

## Troubleshooting

### Issue: "File not found" for temporal query

**Solution**: The file may not have existed at that point in time. Check file history to see when it was first added.

### Issue: Multiple versions at same timestamp

**Solution**: This shouldn't happen as git commits have unique timestamps. If it does, use commit SHA instead.

### Issue: No history available

**Solution**: File may have been ingested only once. Re-ingest after making changes to build history.

## See Also

- [Batch Processing](BATCH_PROCESSING.md) - Batch ingest multiple files
- [Database Backends](DATABASE_BACKENDS.md) - Database schema details
