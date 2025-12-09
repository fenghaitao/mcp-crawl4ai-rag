# Implementation Plan: Batch Processing and Query System

## Overview

This implementation plan breaks down the batch processing and query system into discrete, manageable tasks. Each task builds incrementally on previous work, with clear objectives and requirements references.

---

## Phase 1: Database Schema and Foundation

- [x] 1. Update database schema files
  - Create `database/schema/000_repositories_table.sql` with repositories table definition
  - Update `database/schema/001_files_table.sql` to add temporal fields (valid_from, valid_until, commit_sha, repo_id)
  - Update `database/schema/002_content_chunks.sql` to use file_id foreign key properly
  - Include all indexes, constraints, and comments
  - Update unique constraints to (repo_id, commit_sha, file_path) for files table
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement schema application in backends
  - Update `SupabaseBackend.apply_schema()` to handle repositories table (000_repositories_table.sql)
  - Update `ChromaBackend.apply_schema()` to create repositories collection
  - Ensure schema files are applied in correct order (000, 001, 002)
  - _Requirements: 1.1_

- [x] 3. Update CLI commands for schema management
  - Ensure existing `db apply-schema` command works with updated schemas
  - Ensure existing `db drop-schema` command handles repositories table
  - Add confirmation prompts for destructive operations if not already present
  - _Requirements: 1.1_

---

## Phase 2: Git Integration Service

- [x] 4. Create GitService class
  - Create `core/services/git_service.py` with GitService class
  - Implement `detect_repository(file_path)` method
  - Implement `get_commit_info(repo_root)` method
  - Implement `get_remote_url(repo_root)` method
  - Implement `get_relative_path(repo_root, file_path)` method
  - Add error handling for non-git directories
  - _Requirements: 1.1, 1.2_

- [x] 5. Add GitPython dependency
  - Add `gitpython` to `pyproject.toml` dependencies
  - Update installation documentation
  - _Requirements: 1.1_

- [x] 5.1 Write unit tests for GitService
  - Test repository detection with mock git repos
  - Test commit info extraction
  - Test relative path computation
  - Test error handling for non-git directories
  - _Requirements: 1.1, 1.2_

---

## Phase 3: Enhanced Backend Interface

- [x] 6. Add repository methods to DatabaseBackend
  - Add `store_repository(repo_url, repo_name)` abstract method to base class
  - Add `get_repository(repo_url)` abstract method
  - Add `get_repository_by_id(repo_id)` abstract method
  - Add `update_repository_last_ingested(repo_id)` abstract method
  - _Requirements: 1.4_

- [x] 7. Add temporal file methods to DatabaseBackend
  - Add `store_file_version(file_version)` abstract method
  - Add `get_current_file(repo_id, file_path)` abstract method
  - Add `get_file_at_time(repo_id, file_path, timestamp)` abstract method
  - Add `get_file_at_commit(repo_id, file_path, commit_sha)` abstract method
  - Add `get_file_history(repo_id, file_path, limit)` abstract method
  - Add `list_files(repo_id, content_type, current_only, limit, offset)` abstract method
  - _Requirements: 7.1, 7.2, 7.3, 7.1.1, 7.1.2, 8.1, 8.2, 8.3_

- [x] 8. Implement repository methods in SupabaseBackend
  - Implement `store_repository()` with INSERT ON CONFLICT
  - Implement `get_repository()` with SELECT query
  - Implement `get_repository_by_id()` with SELECT query
  - Implement `update_repository_last_ingested()` with UPDATE query
  - _Requirements: 1.4_

- [x] 9. Implement temporal file methods in SupabaseBackend
  - Implement `store_file_version()` with valid_until update logic
  - Implement `get_current_file()` with WHERE valid_until IS NULL
  - Implement `get_file_at_time()` with temporal range query
  - Implement `get_file_at_commit()` with commit_sha filter
  - Implement `get_file_history()` with ORDER BY valid_from DESC
  - Implement `list_files()` with filtering and pagination
  - _Requirements: 7.1, 7.2, 7.3, 7.1.1, 7.1.2, 8.1, 8.2, 8.3_

- [x] 10. Implement repository methods in ChromaBackend
  - Implement `store_repository()` using metadata storage
  - Implement `get_repository()` with metadata query
  - Implement `get_repository_by_id()` with metadata query
  - Implement `update_repository_last_ingested()` with metadata update
  - _Requirements: 1.4_

- [x] 11. Implement temporal file methods in ChromaBackend
  - Implement `store_file_version()` with metadata-based temporal tracking
  - Implement `get_current_file()` with metadata filter
  - Implement `get_file_at_time()` with metadata temporal query
  - Implement `get_file_at_commit()` with metadata commit filter
  - Implement `get_file_history()` with metadata sorting
  - Implement `list_files()` with metadata filtering
  - _Requirements: 7.1, 7.2, 7.3, 7.1.1, 7.1.2, 8.1, 8.2, 8.3_

- [x] 11.1 Write unit tests for backend temporal methods
  - Test file version storage and valid_until updates
  - Test current file retrieval
  - Test temporal queries at specific times
  - Test commit-based queries
  - Test file history retrieval
  - _Requirements: 7.1, 7.2, 7.3, 7.1.1_

---

## Phase 4: Enhanced Document Ingest Service

- [x] 12. Update DocumentIngestService for repository support
  - Add `git_service` parameter to `__init__`
  - Update `ingest_document()` to detect repository
  - Update `ingest_document()` to store repository record
  - Update `ingest_document()` to use relative paths
  - Update `ingest_document()` to set temporal fields (valid_from)
  - Update `ingest_document()` to handle files outside git repos
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 12.1 Write unit tests for enhanced DocumentIngestService
  - Test ingestion with git repository
  - Test ingestion without git repository
  - Test relative path computation
  - Test temporal field setting
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

---

## Phase 5: Batch Processing Service

- [x] 13. Create BatchIngestService class
  - Create `core/services/batch_ingest_service.py`
  - Implement `__init__(backend, git_service, ingest_service)`
  - Define `BatchProgress` dataclass for tracking
  - _Requirements: 2.1, 2.2, 2.3, 13.1, 13.2_

- [x] 14. Implement file discovery
  - Implement `discover_files(directory, pattern, recursive)` method
  - Use `pathlib.Path.glob()` for pattern matching
  - Support multiple patterns (*.md, *.html, *.rst)
  - Return sorted list of file paths
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 15. Implement file validation
  - Implement `validate_file(file_path)` method
  - Check file exists and is readable
  - Check file size within limits (0 < size < 50MB)
  - Check file extension is supported
  - Return dict with 'valid', 'issues', 'warnings'
  - _Requirements: 12.1, 12.2, 12.3, 12.4_

- [x] 16. Implement progress tracking
  - Implement `_load_progress(progress_file)` method
  - Implement `_save_progress(progress_file, file_path)` method
  - Use JSON format for progress file
  - Store completed file paths in set
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 17. Implement batch ingestion logic
  - Implement `ingest_batch(directory, pattern, recursive, force, dry_run, resume)` method
  - Discover files matching pattern
  - Load progress if resume=True
  - Validate files if dry_run=True
  - Process files sequentially with progress updates
  - Handle errors gracefully and continue
  - Save progress after each file
  - Generate error report if failures occurred
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 18. Implement error reporting
  - Implement `_generate_error_report(errors, output_path)` method
  - Write JSON file with error details
  - Include file path, error type, error message
  - Include timestamp and summary statistics
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 18.1 Write unit tests for BatchIngestService
  - Test file discovery with various patterns
  - Test file validation logic
  - Test progress tracking and resume
  - Test error handling and reporting
  - Test dry-run mode
  - Mock file system and backend
  - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3, 12.1, 12.2, 12.3, 13.1, 13.2, 13.3, 13.4, 13.5_

---

## Phase 6: Query Service

- [x] 19. Create QueryService class
  - Create `core/services/query_service.py`
  - Implement `__init__(backend)`
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 20. Implement file query methods
  - Implement `query_file(repo_url, file_path, commit_sha, timestamp)` method
  - Get repository by URL
  - Call appropriate backend method based on parameters
  - Return FileVersion or None
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 21. Implement file listing
  - Implement `list_files(repo_url, content_type, current_only, limit, offset)` method
  - Get repository by URL if specified
  - Call backend list_files with filters
  - Return tuple of (files, total_count)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 22. Implement file history
  - Implement `get_file_history(repo_url, file_path, limit)` method
  - Get repository by URL
  - Call backend get_file_history
  - Return list of FileVersion objects
  - _Requirements: 7.1.1, 7.1.2, 7.1.3, 7.1.4, 7.1.5_

- [x] 23. Implement chunk retrieval
  - Implement `get_file_chunks(file_version_id)` method
  - Query content_chunks by file_id
  - Order by chunk_number
  - Return list of chunk dictionaries
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 24. Implement chunk search
  - Implement `search_chunks(content_type, has_code, metadata_filter, limit)` method
  - Build query with filters
  - Apply AND logic for multiple filters
  - Return list of matching chunks
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 24.1 Write unit tests for QueryService
  - Test file queries with various parameters
  - Test temporal queries
  - Test file listing with filters
  - Test file history retrieval
  - Test chunk retrieval and search
  - Mock backend
  - _Requirements: 7.1, 7.2, 7.3, 7.1.1, 8.1, 9.1, 10.1_

---

## Phase 7: CLI Commands

- [x] 25. Add batch ingest CLI command
  - Add `ingest-docs-dir` command to `core/cli/rag.py`
  - Accept directory path argument
  - Add --pattern option (default: *.md)
  - Add --recursive flag
  - Add --force flag
  - Add --dry-run flag
  - Add --continue flag for resume
  - Display progress with click.progressbar or custom output
  - Display summary statistics at end
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 26. Add query file CLI command
  - Add `query-file` command to `core/cli/rag.py`
  - Accept repo-url and file-path arguments
  - Add --commit option for specific commit
  - Add --timestamp option for point-in-time query
  - Add --json flag for JSON output
  - Display file metadata in table format
  - _Requirements: 7.1, 7.2, 7.3, 11.1, 11.4, 11.5_

- [x] 27. Add list files CLI command
  - Add `list-files` command to `core/cli/rag.py`
  - Add --repo-url option for filtering
  - Add --content-type option for filtering
  - Add --current-only flag (default: true)
  - Add --limit option (default: 100)
  - Add --offset option (default: 0)
  - Add --json flag for JSON output
  - Display files in table format with key metadata
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 11.2, 11.4, 11.5_

- [x] 28. Add file history CLI command
  - Add `file-history` command to `core/cli/rag.py`
  - Accept repo-url and file-path arguments
  - Add --limit option (default: 100)
  - Add --json flag for JSON output
  - Display version history in table format
  - Show commit SHA, valid_from, valid_until, word_count
  - _Requirements: 7.1.1, 7.1.2, 7.1.3, 7.1.4, 7.1.5, 11.3, 11.4, 11.5_

- [x] 29. Add list chunks CLI command
  - Add `list-chunks` command to `core/cli/rag.py`
  - Accept file-id argument
  - Add --json flag for JSON output
  - Display chunks in table format
  - Show chunk_number, word_count, has_code, summary preview
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 11.3, 11.4, 11.5_

---

## Phase 8: Integration and Testing

- [x] 30. Create integration test suite
  - Create `tests/integration/test_batch_query_system.py`
  - Set up test git repository with sample files
  - Test end-to-end batch ingestion
  - Test temporal queries
  - Test file history tracking
  - Test resume capability
  - Clean up test data after tests

- [x] 31. Update documentation
  - Update `README.md` with batch processing examples
  - Update `docs/DATABASE_BACKENDS.md` with new schema info
  - Create `docs/BATCH_PROCESSING.md` with usage guide
  - Create `docs/TEMPORAL_QUERIES.md` with query examples
  - Update CLI help text

- [x] 32. Final checkpoint - Ensure all tests pass
  - Run all unit tests
  - Run all integration tests
  - Verify CLI commands work correctly
  - Test with both Supabase and ChromaDB backends
  - Ask user if questions arise

---

## Summary

**Total Tasks:** 38 tasks (including all unit tests)
**Estimated Complexity:** High
**Key Dependencies:**
- GitPython library
- New database schemas
- Enhanced backend interface

**Implementation Order:**
1. Database foundation (Tasks 1-3)
2. Git integration (Tasks 4-5.1)
3. Backend enhancements (Tasks 6-11.1)
4. Service layer (Tasks 12-24.1)
5. CLI interface (Tasks 25-29)
6. Testing and docs (Tasks 30-32)

**Testing Strategy:**
- Unit tests for each service component
- Integration tests for end-to-end workflows
- Both Supabase and ChromaDB backend testing
