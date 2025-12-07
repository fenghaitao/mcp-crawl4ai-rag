# Design Document: Batch Processing and Query System with Temporal Versioning

## Overview

This design document specifies the architecture for enhancing the documentation ingestion system with batch processing capabilities and a comprehensive query interface. The system implements a temporal versioning model inspired by Graphiti, allowing users to track documentation evolution across git commits and query documents at specific points in time.

The enhancement builds on the existing `DocumentIngestService` and backend abstraction layer, adding:
1. **Repository tracking** with git integration
2. **Temporal versioning** with valid_from/valid_until timestamps
3. **Batch processing** with progress tracking and resume capability
4. **Query service** for retrieving files and chunks with temporal constraints
5. **CLI commands** for batch operations and inspection

## Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ ingest-docs  │  │ query-docs   │  │ list-docs    │     │
│  │   (batch)    │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ BatchIngestSvc   │  │ QueryService     │                │
│  │ - File discovery │  │ - Temporal query │                │
│  │ - Progress track │  │ - File history   │                │
│  │ - Validation     │  │ - Chunk retrieval│                │
│  └──────────────────┘  └──────────────────┘                │
│           │                      │                           │
│           ▼                      ▼                           │
│  ┌──────────────────────────────────────┐                  │
│  │    DocumentIngestService             │                  │
│  │    (existing, enhanced)              │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ DatabaseBackend  │  │ GitService       │                │
│  │ (abstract)       │  │ - Detect repo    │                │
│  │                  │  │ - Get commit SHA │                │
│  └──────────────────┘  │ - Get timestamp  │                │
│           │             └──────────────────┘                │
│           ▼                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ SupabaseBackend  │  │ ChromaBackend    │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**BatchIngestService:**
- Discover files matching patterns
- Validate files before processing
- Track progress with resume capability
- Coordinate with DocumentIngestService
- Generate error reports

**QueryService:**
- Query files by path with temporal constraints
- List files with filtering and pagination
- Retrieve file history
- Get chunks for specific files
- Search chunks by metadata

**GitService:**
- Detect git repository root
- Extract commit SHA and timestamp
- Compute relative paths
- Validate repository state

**Enhanced DatabaseBackend:**
- Store/query repositories table
- Store/query files with temporal fields
- Implement temporal query logic
- Manage valid_from/valid_until updates

## Data Models

### Database Schema

#### repositories table

```sql
CREATE TABLE repositories (
    id BIGSERIAL PRIMARY KEY,
    repo_url TEXT NOT NULL UNIQUE,              -- Git remote URL
    repo_name TEXT NOT NULL,                    -- Repository name (extracted from URL)
    description TEXT,                           -- Optional description
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_repositories_url ON repositories(repo_url);
CREATE INDEX idx_repositories_name ON repositories(repo_name);

COMMENT ON TABLE repositories IS 'Git repositories containing documentation and source code';
COMMENT ON COLUMN repositories.repo_url IS 'Git remote URL (e.g., https://github.com/user/repo.git)';
COMMENT ON COLUMN repositories.repo_name IS 'Repository name for display (e.g., simics-docs)';
COMMENT ON COLUMN repositories.last_ingested_at IS 'Last time we ingested files from this repository';
```

#### files table (enhanced)

```sql
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT NOT NULL,                    -- Foreign key to repositories
    commit_sha TEXT NOT NULL,                   -- Git commit SHA
    file_path TEXT NOT NULL,                    -- Relative path from repo root
    content_hash TEXT NOT NULL,                 -- SHA256 hash of file content
    file_size BIGINT NOT NULL,                  -- File size in bytes
    word_count INTEGER NOT NULL DEFAULT 0,      -- Total word count
    chunk_count INTEGER NOT NULL DEFAULT 0,     -- Number of chunks
    content_type VARCHAR(50) NOT NULL,          -- 'code_dml', 'python_test', 'documentation'
    
    -- Temporal fields
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,    -- When this version became valid
    valid_until TIMESTAMP WITH TIME ZONE,            -- When superseded (NULL if current)
    
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (repo_id) REFERENCES repositories(repo_id) ON DELETE CASCADE,
    UNIQUE(repo_id, commit_sha, file_path),     -- Unique version identifier
    CHECK (file_size >= 0),
    CHECK (word_count >= 0),
    CHECK (chunk_count >= 0),
    CHECK (content_type IN ('code_dml', 'python_test', 'documentation')),
    CHECK (valid_until IS NULL OR valid_until > valid_from)
);

-- Indexes for performance
CREATE INDEX idx_files_repo_id ON files(repo_id);
CREATE INDEX idx_files_commit_sha ON files(commit_sha);
CREATE INDEX idx_files_file_path ON files(file_path);
CREATE INDEX idx_files_content_type ON files(content_type);
CREATE INDEX idx_files_valid_from ON files(valid_from);
CREATE INDEX idx_files_valid_until ON files(valid_until);
CREATE INDEX idx_files_current ON files(repo_id, file_path) WHERE valid_until IS NULL;

COMMENT ON TABLE files IS 'File versions with temporal validity tracking';
COMMENT ON COLUMN files.file_path IS 'Path relative to repository root';
COMMENT ON COLUMN files.valid_from IS 'Timestamp when this version became valid (commit timestamp)';
COMMENT ON COLUMN files.valid_until IS 'Timestamp when superseded by newer version (NULL if current)';
```

#### content_chunks table (redesigned)

```sql
CREATE TABLE content_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL,                    -- Reference to files table
    chunk_number INTEGER NOT NULL,              -- Sequential number within file
    content TEXT NOT NULL,                      -- Chunk text content
    content_type VARCHAR(50) NOT NULL,          -- 'code_dml', 'python_test', 'documentation'
    summary TEXT,                               -- LLM-generated summary (optional)
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB, -- Additional metadata
    embedding vector(1536),                     -- Vector embedding for semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, chunk_number),              -- Prevent duplicate chunks per file
    CHECK (chunk_number >= 0),
    CHECK (content_type IN ('code_dml', 'python_test', 'documentation'))
);

-- Indexes for performance
CREATE INDEX idx_content_chunks_file_id ON content_chunks(file_id);
CREATE INDEX idx_content_chunks_content_type ON content_chunks(content_type);
CREATE INDEX idx_content_chunks_created_at ON content_chunks(created_at);
CREATE INDEX idx_content_chunks_metadata ON content_chunks USING gin (metadata);

-- Partial indexes for type-specific queries
CREATE INDEX idx_content_chunks_code_dml ON content_chunks(file_id, chunk_number) 
    WHERE content_type = 'code_dml';
CREATE INDEX idx_content_chunks_python ON content_chunks(file_id, chunk_number) 
    WHERE content_type = 'python_test';
CREATE INDEX idx_content_chunks_docs ON content_chunks(file_id, chunk_number) 
    WHERE content_type = 'documentation';

-- Vector similarity search index (pgvector)
CREATE INDEX idx_content_chunks_embedding ON content_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE content_chunks IS 'Text chunks with embeddings for RAG operations';
COMMENT ON COLUMN content_chunks.file_id IS 'Reference to specific file version';
COMMENT ON COLUMN content_chunks.chunk_number IS 'Sequential number of this chunk within the file';
COMMENT ON COLUMN content_chunks.metadata IS 'JSONB metadata (title, section, word_count, has_code, etc.)';
COMMENT ON COLUMN content_chunks.embedding IS 'Vector embedding for semantic similarity search';
```

### Python Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pathlib import Path

@dataclass
class Repository:
    """Represents a git repository."""
    repo_id: Optional[int]
    repo_url: str
    created_at: datetime
    last_seen_at: datetime

@dataclass
class FileVersion:
    """Represents a specific version of a file."""
    id: Optional[int]
    repo_id: int
    commit_sha: str
    file_path: str  # Relative to repo root
    content_hash: str
    file_size: int
    word_count: int
    chunk_count: int
    content_type: str
    valid_from: datetime
    valid_until: Optional[datetime]
    ingested_at: datetime

@dataclass
class GitInfo:
    """Git repository information."""
    repo_root: Path
    repo_url: str
    commit_sha: str
    commit_timestamp: datetime
    
    def get_relative_path(self, file_path: Path) -> str:
        """Get path relative to repository root."""
        return str(file_path.relative_to(self.repo_root))

@dataclass
class BatchProgress:
    """Progress tracking for batch operations."""
    total_files: int
    processed: int
    succeeded: int
    failed: int
    skipped: int
    errors: List[dict]
    start_time: datetime
    
    @property
    def progress_percent(self) -> float:
        return (self.processed / self.total_files * 100) if self.total_files > 0 else 0.0
```

## Components and Interfaces

### GitService

```python
class GitService:
    """Service for git repository operations."""
    
    def detect_repository(self, file_path: Path) -> Optional[GitInfo]:
        """
        Detect git repository for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            GitInfo if file is in a git repository, None otherwise
        """
        pass
    
    def get_commit_info(self, repo_root: Path) -> tuple[str, datetime]:
        """
        Get current commit SHA and timestamp.
        
        Args:
            repo_root: Path to repository root
            
        Returns:
            Tuple of (commit_sha, commit_timestamp)
        """
        pass
    
    def get_remote_url(self, repo_root: Path) -> str:
        """
        Get git remote URL.
        
        Args:
            repo_root: Path to repository root
            
        Returns:
            Remote URL (e.g., https://github.com/user/repo.git)
        """
        pass
```

### Enhanced DatabaseBackend Interface

```python
from abc import abstractmethod

class DatabaseBackend(ABC):
    """Enhanced backend interface with repository and temporal support."""
    
    # Repository operations
    @abstractmethod
    def store_repository(self, repo_url: str) -> int:
        """Store repository record and return repo_id."""
        pass
    
    @abstractmethod
    def get_repository(self, repo_url: str) -> Optional[Repository]:
        """Get repository by URL."""
        pass
    
    @abstractmethod
    def update_repository_last_seen(self, repo_id: int) -> bool:
        """Update last_seen_at timestamp."""
        pass
    
    # File operations with temporal support
    @abstractmethod
    def store_file_version(self, file_version: FileVersion) -> int:
        """
        Store new file version and update previous version's valid_until.
        
        Returns:
            File version ID
        """
        pass
    
    @abstractmethod
    def get_current_file(self, repo_id: int, file_path: str) -> Optional[FileVersion]:
        """Get currently valid version of a file (valid_until IS NULL)."""
        pass
    
    @abstractmethod
    def get_file_at_time(self, repo_id: int, file_path: str, timestamp: datetime) -> Optional[FileVersion]:
        """Get file version valid at specific timestamp."""
        pass
    
    @abstractmethod
    def get_file_at_commit(self, repo_id: int, file_path: str, commit_sha: str) -> Optional[FileVersion]:
        """Get file version from specific commit."""
        pass
    
    @abstractmethod
    def get_file_history(self, repo_id: int, file_path: str, limit: int = 100) -> List[FileVersion]:
        """Get all versions of a file ordered by valid_from."""
        pass
    
    @abstractmethod
    def list_files(self, repo_id: Optional[int] = None, content_type: Optional[str] = None,
                   current_only: bool = True, limit: int = 100, offset: int = 0) -> tuple[List[FileVersion], int]:
        """
        List files with filtering and pagination.
        
        Returns:
            Tuple of (file_list, total_count)
        """
        pass
```

### BatchIngestService

```python
class BatchIngestService:
    """Service for batch document ingestion."""
    
    def __init__(self, backend: DatabaseBackend, git_service: GitService):
        self.backend = backend
        self.git_service = git_service
        self.ingest_service = DocumentIngestService(backend)
    
    def discover_files(self, directory: Path, pattern: str = "*.md", 
                      recursive: bool = True) -> List[Path]:
        """
        Discover files matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (e.g., *.md, *.html)
            recursive: Whether to search subdirectories
            
        Returns:
            List of file paths
        """
        pass
    
    def validate_file(self, file_path: Path) -> dict:
        """
        Validate file before processing.
        
        Returns:
            Dict with 'valid', 'issues', 'warnings'
        """
        pass
    
    def ingest_batch(self, directory: Path, pattern: str = "*.md",
                    recursive: bool = True, force: bool = False,
                    dry_run: bool = False, resume: bool = False) -> BatchProgress:
        """
        Ingest multiple files with progress tracking.
        
        Args:
            directory: Directory containing files
            pattern: File pattern to match
            recursive: Search subdirectories
            force: Force reprocess existing files
            dry_run: Validate without processing
            resume: Resume from previous progress
            
        Returns:
            BatchProgress with results
        """
        pass
    
    def _load_progress(self, progress_file: Path) -> set:
        """Load completed files from progress file."""
        pass
    
    def _save_progress(self, progress_file: Path, file_path: str):
        """Save completed file to progress file."""
        pass
    
    def _generate_error_report(self, errors: List[dict], output_path: Path):
        """Generate error report file."""
        pass
```

### QueryService

```python
class QueryService:
    """Service for querying ingested documents."""
    
    def __init__(self, backend: DatabaseBackend):
        self.backend = backend
    
    def query_file(self, repo_url: str, file_path: str,
                  commit_sha: Optional[str] = None,
                  timestamp: Optional[datetime] = None) -> Optional[FileVersion]:
        """
        Query file with temporal constraints.
        
        Args:
            repo_url: Repository URL
            file_path: Relative file path
            commit_sha: Specific commit (optional)
            timestamp: Point in time (optional)
            
        Returns:
            FileVersion or None
        """
        pass
    
    def list_files(self, repo_url: Optional[str] = None,
                  content_type: Optional[str] = None,
                  current_only: bool = True,
                  limit: int = 100, offset: int = 0) -> tuple[List[FileVersion], int]:
        """
        List files with filtering.
        
        Returns:
            Tuple of (files, total_count)
        """
        pass
    
    def get_file_history(self, repo_url: str, file_path: str,
                        limit: int = 100) -> List[FileVersion]:
        """Get version history for a file."""
        pass
    
    def get_file_chunks(self, file_version_id: int) -> List[dict]:
        """Get all chunks for a specific file version."""
        pass
    
    def search_chunks(self, content_type: Optional[str] = None,
                     has_code: Optional[bool] = None,
                     metadata_filter: Optional[dict] = None,
                     limit: int = 100) -> List[dict]:
        """Search chunks by metadata."""
        pass
```

## Error Handling

### Validation Errors

```python
class ValidationError(Exception):
    """Raised when file validation fails."""
    pass

class GitRepositoryError(Exception):
    """Raised when git operations fail."""
    pass

class TemporalQueryError(Exception):
    """Raised when temporal query constraints are invalid."""
    pass
```

### Error Recovery

1. **File Processing Errors:**
   - Log error with file path and message
   - Continue processing remaining files
   - Generate error report at end

2. **Git Detection Errors:**
   - Fall back to treating as standalone file
   - Use file system path as identifier
   - Warn user about missing git context

3. **Database Errors:**
   - Rollback partial transactions
   - Preserve progress file
   - Allow resume from last successful file

## Testing Strategy

### Unit Tests

1. **GitService Tests:**
   - Test repository detection
   - Test commit info extraction
   - Test relative path computation
   - Mock git commands

2. **BatchIngestService Tests:**
   - Test file discovery with patterns
   - Test validation logic
   - Test progress tracking
   - Test resume capability
   - Mock file system and backend

3. **QueryService Tests:**
   - Test temporal queries
   - Test file history retrieval
   - Test filtering and pagination
   - Mock backend

4. **Backend Tests:**
   - Test repository CRUD operations
   - Test file version storage
   - Test temporal query logic
   - Test valid_until updates

### Integration Tests

1. **End-to-End Batch Ingestion:**
   - Create test git repository
   - Ingest files in batch
   - Verify all files stored correctly
   - Verify temporal fields set properly

2. **Temporal Query Scenarios:**
   - Ingest multiple versions of same file
   - Query current version
   - Query historical versions
   - Verify valid_until updates

3. **Resume Capability:**
   - Start batch ingestion
   - Interrupt mid-process
   - Resume and verify no duplicates

## Implementation Notes

### Git Integration

Use `GitPython` library for git operations:

```python
import git
from datetime import datetime

def detect_repository(file_path: Path) -> Optional[GitInfo]:
    try:
        repo = git.Repo(file_path, search_parent_directories=True)
        commit = repo.head.commit
        
        return GitInfo(
            repo_root=Path(repo.working_dir),
            repo_url=repo.remotes.origin.url,
            commit_sha=commit.hexsha,
            commit_timestamp=datetime.fromtimestamp(commit.committed_date)
        )
    except git.InvalidGitRepositoryError:
        return None
```

### Temporal Query Implementation

```sql
-- Get current version
SELECT * FROM files 
WHERE repo_id = ? AND file_path = ? AND valid_until IS NULL;

-- Get version at specific time
SELECT * FROM files
WHERE repo_id = ? AND file_path = ?
  AND valid_from <= ? AND (valid_until IS NULL OR valid_until > ?)
ORDER BY valid_from DESC
LIMIT 1;

-- Get version by commit
SELECT * FROM files
WHERE repo_id = ? AND file_path = ? AND commit_sha = ?;

-- Get file history
SELECT * FROM files
WHERE repo_id = ? AND file_path = ?
ORDER BY valid_from DESC
LIMIT ?;
```

### Progress File Format

```json
{
  "version": "1.0",
  "started_at": "2025-01-15T10:30:00Z",
  "directory": "/path/to/docs",
  "pattern": "*.md",
  "completed_files": [
    "/path/to/docs/file1.md",
    "/path/to/docs/file2.md"
  ],
  "total_discovered": 100,
  "last_updated": "2025-01-15T10:35:00Z"
}
```

## Performance Considerations

1. **Batch Size:** Process files sequentially to avoid memory issues
2. **Index Strategy:** Create indexes on temporal fields for fast queries
3. **Pagination:** Implement cursor-based pagination for large result sets
4. **Caching:** Cache repository lookups to avoid repeated git operations
5. **Parallel Processing:** Future enhancement for parallel file processing

## Clean Slate Approach

This design starts fresh with optimized schemas. No migration from existing data is required.

**Benefits:**
- Clean, normalized schema design
- Optimized indexes from the start
- No legacy compatibility concerns
- Temporal model built-in from day one

**Implementation Order:**
1. Create new database schemas (repositories, files, content_chunks)
2. Implement GitService for repository operations
3. Implement BatchIngestService with progress tracking
4. Implement QueryService with temporal support
5. Add CLI commands for batch and query operations
6. Add comprehensive tests

## Future Enhancements

1. **Parallel Processing:** Use multiprocessing for faster batch ingestion
2. **Incremental Updates:** Detect changed files using git diff
3. **Branch Support:** Track files across different git branches
4. **Diff Visualization:** Show changes between file versions
5. **Retention Policies:** Automatically archive old versions
