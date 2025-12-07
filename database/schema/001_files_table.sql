-- Files table to track individual files and their metadata with temporal versioning
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT NOT NULL,                           -- Foreign key to repositories
    commit_sha TEXT NOT NULL,                          -- Git commit SHA
    file_path TEXT NOT NULL,                           -- Relative path from repo root
    content_hash TEXT NOT NULL,                        -- SHA256 hash of file content
    file_size BIGINT NOT NULL,                         -- File size in bytes
    word_count INTEGER NOT NULL DEFAULT 0,             -- Total word count
    chunk_count INTEGER NOT NULL DEFAULT 0,            -- Number of chunks
    content_type VARCHAR(50) NOT NULL,                 -- 'code_dml', 'python_test', 'documentation'
    
    -- Temporal fields
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,      -- When this version became valid
    valid_until TIMESTAMP WITH TIME ZONE,              -- When superseded (NULL if current)
    
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE,
    UNIQUE(repo_id, commit_sha, file_path),            -- Unique version identifier
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
CREATE INDEX idx_files_content_hash ON files(content_hash);
CREATE INDEX idx_files_valid_from ON files(valid_from);
CREATE INDEX idx_files_valid_until ON files(valid_until);
CREATE INDEX idx_files_current ON files(repo_id, file_path) WHERE valid_until IS NULL;
CREATE INDEX idx_files_ingested_at ON files(ingested_at);

-- Comments for documentation
COMMENT ON TABLE files IS 'File versions with temporal validity tracking';
COMMENT ON COLUMN files.file_path IS 'Path relative to repository root';
COMMENT ON COLUMN files.content_hash IS 'SHA256 hash for change detection and deduplication';
COMMENT ON COLUMN files.content_type IS 'Type of content: code_dml, python_test, or documentation';
COMMENT ON COLUMN files.chunk_count IS 'Number of chunks generated from this file';
COMMENT ON COLUMN files.valid_from IS 'Timestamp when this version became valid (commit timestamp)';
COMMENT ON COLUMN files.valid_until IS 'Timestamp when superseded by newer version (NULL if current)';