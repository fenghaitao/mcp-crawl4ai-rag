-- Files table to track individual files and their metadata
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,                    -- Absolute or relative path to the file
    content_hash TEXT NOT NULL,                        -- SHA256 hash of file content for change detection
    file_size BIGINT NOT NULL,                         -- File size in bytes
    word_count INTEGER NOT NULL DEFAULT 0,             -- Total word count in the file
    chunk_count INTEGER NOT NULL DEFAULT 0,            -- Number of chunks generated from this file
    content_type VARCHAR(50) NOT NULL,                 -- 'code_dml', 'python_test', 'documentation'
    source_id TEXT NOT NULL,                           -- Foreign key to sources table
    last_modified TIMESTAMP WITH TIME ZONE,            -- File system modification time
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE,
    CHECK (file_size >= 0),
    CHECK (word_count >= 0),
    CHECK (chunk_count >= 0),
    CHECK (content_type IN ('code_dml', 'python_test', 'documentation'))
);

-- Indexes for performance
CREATE INDEX idx_files_source_id ON files(source_id);
CREATE INDEX idx_files_content_type ON files(content_type);
CREATE INDEX idx_files_content_hash ON files(content_hash);
CREATE INDEX idx_files_ingested_at ON files(ingested_at);
CREATE INDEX idx_files_file_path ON files(file_path);

-- Comments for documentation
COMMENT ON TABLE files IS 'Tracks individual files ingested into the RAG system';
COMMENT ON COLUMN files.file_path IS 'Unique path to the source file';
COMMENT ON COLUMN files.content_hash IS 'SHA256 hash for change detection and deduplication';
COMMENT ON COLUMN files.content_type IS 'Type of content: code_dml, python_test, or documentation';
COMMENT ON COLUMN files.chunk_count IS 'Number of chunks generated from this file';