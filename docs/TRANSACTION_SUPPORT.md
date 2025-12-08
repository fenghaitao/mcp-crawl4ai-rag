# Database Transaction Support

## Overview

The RAG system supports database transactions through a context manager API. However, transaction support varies by backend.

## API Usage

```python
# Use transactions for atomic operations
with backend.transaction():
    file_id = backend.store_file_version(file_data)
    backend.store_chunks(file_id, chunks)
    # If any operation fails, transaction is rolled back (Supabase only)
```

## Backend Support

### Supabase (PostgreSQL)

**Status**: ⚠️ **Partial Support**

- PostgreSQL supports full ACID transactions
- Current implementation: **Best-effort** (no rollback)
- **TODO**: Implement proper transactions using psycopg2

**Why not fully implemented?**
- Supabase Python client doesn't expose transaction API
- Need to use psycopg2 directly with connection string
- Requires additional dependency and connection management

**Workaround**:
- Operations are idempotent where possible
- Database constraints prevent most inconsistencies
- Foreign key cascades handle cleanup

### ChromaDB

**Status**: ❌ **Not Supported**

- ChromaDB is a vector database, not a relational database
- No transaction support
- Operations are executed immediately
- **Cannot be rolled back**

**Mitigation**:
- Operations are designed to be atomic where possible
- Cleanup methods available for manual recovery
- Retry logic handles transient failures

## Critical Operations

### 1. File Ingestion

**Operations**:
1. Store file version record
2. Store chunks with embeddings

**Risk**: If step 2 fails, orphaned file record exists

**Mitigation**:
- `store_file_version` validates data before storing
- Retry logic attempts multiple times
- Manual cleanup: `egest-doc` removes orphaned records

### 2. File Removal

**Operations**:
1. Delete all chunks for file
2. Delete file record

**Risk**: If step 1 fails, orphaned chunks exist

**Mitigation**:
- Delete chunks first (safer order)
- Type conversion ensures proper matching
- Both operations are idempotent

### 3. Version Updates

**Operations**:
1. Set `valid_until` on old version
2. Create new version record

**Risk**: If step 2 fails, old version incorrectly closed

**Mitigation**:
- ChromaDB: Best-effort, logs errors
- Supabase: Database constraints prevent invalid states
- Query methods handle edge cases

## Future Improvements

### Short Term
1. Add proper PostgreSQL transaction support using psycopg2
2. Implement compensating transactions for ChromaDB
3. Add transaction logging for debugging

### Long Term
1. Consider using a proper relational database for metadata
2. Keep ChromaDB only for vector embeddings
3. Implement two-phase commit for distributed consistency

## Recommendations

### For Production Use

1. **Use Supabase/PostgreSQL** for critical data
   - Better consistency guarantees
   - Proper transaction support (once implemented)
   - ACID compliance

2. **ChromaDB for embeddings only**
   - Keep metadata in PostgreSQL
   - Use ChromaDB only for vector search
   - Sync embeddings asynchronously

3. **Implement idempotency**
   - Design operations to be safely retried
   - Use unique constraints
   - Check before insert/update

4. **Add monitoring**
   - Log transaction failures
   - Alert on orphaned records
   - Periodic consistency checks

## Example: Proper Transaction Implementation (TODO)

```python
# Future implementation with psycopg2
import psycopg2
from contextlib import contextmanager

class SupabaseBackend(DatabaseBackend):
    def __init__(self):
        self._conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        self._conn.autocommit = False  # Enable transactions
    
    @contextmanager
    def transaction(self):
        """Proper PostgreSQL transaction support."""
        try:
            yield self
            self._conn.commit()  # Commit on success
        except Exception as e:
            self._conn.rollback()  # Rollback on failure
            raise
```

## Current Limitations

⚠️ **Important**: The current transaction API is a **compatibility layer** only.

- **ChromaDB**: No rollback capability
- **Supabase**: No rollback capability (yet)
- Operations are **not atomic** across multiple calls
- Failures can leave database in inconsistent state

**Use with caution in production!**
