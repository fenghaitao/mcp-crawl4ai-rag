# Requirements Document

## Introduction

This document specifies requirements for enhancing the documentation ingestion system with batch processing and query capabilities. The system currently supports single-file ingestion through the `ingest-doc` command. This enhancement adds the ability to process multiple files efficiently and query ingested documents through a unified interface. The solution targets scenarios where users need to ingest entire documentation directories and retrieve specific documents or chunks based on various criteria.

## Glossary

- **Batch Processing**: The ability to process multiple files in a single operation with progress tracking and error handling
- **Document Ingest Service**: The service responsible for processing and storing documentation files in the RAG system
- **Backend**: The database abstraction layer (ChromaDB or Supabase) that stores files and chunks
- **Repository**: A git repository containing documentation or source code files
- **Repository Record**: A database entry tracking a repository's URL and metadata
- **File Record**: A database entry tracking a single file's metadata, hash, and processing statistics relative to a repository at a specific commit
- **Content Chunk**: A semantically coherent segment of a document with embeddings and metadata
- **Query Service**: The service responsible for retrieving documents and chunks based on search criteria and temporal constraints
- **Progress Tracking**: The mechanism for monitoring batch operation status and enabling resume capability
- **Content Type**: The classification of files (documentation, code_dml, python_test)
- **File Hash**: SHA256 hash of file content used for change detection and deduplication
- **Git Commit SHA**: The unique identifier for a specific commit in a git repository
- **Relative Path**: File path relative to the repository root directory
- **Temporal Validity**: The time period during which a file version is considered current and valid
- **Valid From**: The timestamp when a file version became valid (typically the git commit timestamp)
- **Valid Until**: The timestamp when a file version was superseded by a newer version (NULL if current)

## Requirements

### Requirement 1

**User Story:** As a documentation maintainer, I want to track documentation files with full temporal versioning, so that I can query documentation at specific points in time and track evolution across commits.

#### Acceptance Criteria

1. WHEN the system ingests files from a git repository THEN the system SHALL detect the repository root directory
2. WHEN the system detects a repository THEN the system SHALL extract the current git commit SHA and commit timestamp
3. WHEN the system stores a file record THEN the system SHALL store the file path relative to the repository root
4. WHEN the system stores a file record THEN the system SHALL set valid_from to the git commit timestamp
5. WHEN the system stores a new version of an existing file THEN the system SHALL set valid_until on the previous version to the new commit timestamp

### Requirement 2

**User Story:** As a documentation maintainer, I want to ingest multiple documentation files in a single command, so that I can efficiently process entire documentation directories.

#### Acceptance Criteria

1. WHEN the CLI receives a directory path THEN the system SHALL discover all documentation files matching the specified pattern
2. WHEN the system processes a directory recursively THEN the system SHALL traverse all subdirectories to find matching files
3. WHEN the system discovers files THEN the system SHALL filter by file extension patterns (e.g., *.md, *.html, *.rst)
4. WHEN the system processes multiple files THEN the system SHALL process them sequentially with clear progress indication
5. WHEN the system completes batch processing THEN the system SHALL report total files processed, succeeded, failed, and skipped

### Requirement 3

**User Story:** As a documentation maintainer, I want to see real-time progress during batch ingestion, so that I can monitor the operation and estimate completion time.

#### Acceptance Criteria

1. WHEN the system starts batch processing THEN the system SHALL display the total number of files to process
2. WHEN the system processes each file THEN the system SHALL display the current file name and progress percentage
3. WHEN the system completes a file THEN the system SHALL display processing time and statistics (chunks, words)
4. WHEN the system encounters an error THEN the system SHALL display the error message and continue with remaining files
5. WHEN the system completes batch processing THEN the system SHALL display a summary with total time and aggregate statistics

### Requirement 4

**User Story:** As a documentation maintainer, I want batch operations to be resumable, so that I can recover from interruptions without reprocessing completed files.

#### Acceptance Criteria

1. WHEN the system starts batch processing THEN the system SHALL create a progress tracking file in the working directory
2. WHEN the system completes processing a file THEN the system SHALL record the file path in the progress tracking file
3. WHEN the system is interrupted THEN the system SHALL preserve the progress tracking file
4. WHEN the system restarts batch processing THEN the system SHALL skip files already recorded in the progress tracking file
5. WHEN the system completes all files THEN the system SHALL remove the progress tracking file

### Requirement 5

**User Story:** As a documentation maintainer, I want to control batch processing behavior, so that I can optimize for different scenarios.

#### Acceptance Criteria

1. WHEN the CLI is invoked THEN the system SHALL accept a --force flag to reprocess all files regardless of existing records
2. WHEN the CLI is invoked THEN the system SHALL accept a --pattern option to specify file matching patterns
3. WHEN the CLI is invoked THEN the system SHALL accept a --recursive flag to enable subdirectory traversal
4. WHEN the CLI is invoked THEN the system SHALL accept a --dry-run flag to preview files without processing
5. WHEN the CLI is invoked THEN the system SHALL accept a --continue flag to resume from previous progress

### Requirement 6

**User Story:** As a documentation maintainer, I want detailed error reporting for batch operations, so that I can identify and fix problematic files.

#### Acceptance Criteria

1. WHEN the system encounters a processing error THEN the system SHALL log the file path and error message
2. WHEN the system completes batch processing THEN the system SHALL generate an error report file if any failures occurred
3. WHEN the system writes an error report THEN the system SHALL include file path, error type, and error message for each failure
4. WHEN the system encounters validation errors THEN the system SHALL distinguish between validation failures and processing failures
5. WHEN the system completes with errors THEN the system SHALL exit with a non-zero status code

### Requirement 7

**User Story:** As a developer, I want to query ingested documents by repository and relative path with temporal constraints, so that I can retrieve specific document versions and their metadata.

#### Acceptance Criteria

1. WHEN the backend receives a file path query without temporal constraint THEN the system SHALL return the currently valid version (valid_until IS NULL)
2. WHEN the backend receives a file path query with a specific timestamp THEN the system SHALL return the version valid at that time
3. WHEN the backend receives a file path query with a commit SHA THEN the system SHALL return the version from that commit
4. WHEN the backend returns a file record THEN the system SHALL include file metadata (relative path, hash, size, content type)
5. WHEN the backend returns a file record THEN the system SHALL include temporal information (valid_from, valid_until, commit_sha)

### Requirement 7.1

**User Story:** As a developer, I want to query the history of a specific file, so that I can see how documentation evolved over time.

#### Acceptance Criteria

1. WHEN the backend receives a file history query THEN the system SHALL return all versions of that file ordered by valid_from
2. WHEN the backend returns file history THEN the system SHALL include commit SHA for each version
3. WHEN the backend returns file history THEN the system SHALL include validity periods for each version
4. WHEN the backend returns file history THEN the system SHALL include change statistics (chunks added/removed, word count delta)
5. WHEN the backend returns file history THEN the system SHALL support pagination for files with many versions

### Requirement 8

**User Story:** As a developer, I want to list all ingested files with filtering options, so that I can discover and manage documents in the system.

#### Acceptance Criteria

1. WHEN the backend receives a list request THEN the system SHALL return all file records up to the specified limit
2. WHEN the backend receives a list request with content type filter THEN the system SHALL return only files matching that content type
3. WHEN the backend receives a list request with repository filter THEN the system SHALL return only files from that repository
4. WHEN the backend returns file records THEN the system SHALL order results by ingestion date (newest first)
5. WHEN the backend returns file records THEN the system SHALL include pagination support for large result sets

### Requirement 9

**User Story:** As a developer, I want to retrieve all chunks for a specific file, so that I can inspect the chunking results and debug issues.

#### Acceptance Criteria

1. WHEN the backend receives a file path THEN the system SHALL return all chunks associated with that file
2. WHEN the backend returns chunks THEN the system SHALL order them by chunk number
3. WHEN the backend returns chunks THEN the system SHALL include chunk content, metadata, and embeddings
4. WHEN the backend returns chunks THEN the system SHALL include chunk-level statistics (word count, has_code)
5. WHEN the backend receives a query for a non-existent file THEN the system SHALL return an empty list

### Requirement 10

**User Story:** As a developer, I want to search chunks by content type and metadata, so that I can filter results for specific use cases.

#### Acceptance Criteria

1. WHEN the backend receives a content type filter THEN the system SHALL return only chunks matching that content type
2. WHEN the backend receives a metadata filter THEN the system SHALL return only chunks where metadata matches the criteria
3. WHEN the backend receives multiple filters THEN the system SHALL apply all filters with AND logic
4. WHEN the backend receives a has_code filter THEN the system SHALL return only chunks containing code blocks
5. WHEN the backend receives a section filter THEN the system SHALL return only chunks from matching section hierarchies

### Requirement 11

**User Story:** As a CLI user, I want to query ingested documents from the command line, so that I can inspect and verify ingestion results.

#### Acceptance Criteria

1. WHEN the CLI receives a query command with file path THEN the system SHALL display the file record and statistics
2. WHEN the CLI receives a list command THEN the system SHALL display all ingested files with key metadata
3. WHEN the CLI receives a chunks command with file path THEN the system SHALL display all chunks for that file
4. WHEN the CLI displays results THEN the system SHALL format output in a readable table format
5. WHEN the CLI receives a --json flag THEN the system SHALL output results in JSON format for programmatic use

### Requirement 12

**User Story:** As a documentation maintainer, I want to validate files before batch ingestion, so that I can identify issues early and avoid partial failures.

#### Acceptance Criteria

1. WHEN the system validates a file THEN the system SHALL check that the file exists and is readable
2. WHEN the system validates a file THEN the system SHALL check that the file size is within acceptable limits
3. WHEN the system validates a file THEN the system SHALL check that the file format is supported
4. WHEN the system validates a file THEN the system SHALL return validation status with issues and warnings
5. WHEN the system runs in dry-run mode THEN the system SHALL validate all files and report issues without processing

### Requirement 13

**User Story:** As a developer, I want the batch processing service to be testable, so that I can ensure reliability and correctness.

#### Acceptance Criteria

1. WHEN the batch service is designed THEN the system SHALL separate file discovery from processing logic
2. WHEN the batch service is designed THEN the system SHALL inject dependencies (backend, chunker) for testability
3. WHEN the batch service processes files THEN the system SHALL emit events for progress tracking
4. WHEN the batch service encounters errors THEN the system SHALL handle exceptions gracefully without crashing
5. WHEN the batch service is tested THEN the system SHALL support mock backends for unit testing
