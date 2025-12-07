-- Content chunks table for file-based RAG operations with temporal versioning support
CREATE TABLE content_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL,                           -- Reference to files table
    chunk_number INTEGER NOT NULL,                     -- Sequential number within file
    content TEXT NOT NULL,                             -- Chunk text content
    content_type VARCHAR(50) NOT NULL,                 -- 'code_dml', 'python_test', 'documentation'
    summary TEXT,                                      -- LLM-generated summary (optional)
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,       -- Additional metadata
    embedding vector(1536),                            -- Vector embedding for semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, chunk_number),                     -- Prevent duplicate chunks per file
    CHECK (chunk_number >= 0),
    CHECK (content_type IN ('code_dml', 'python_test', 'documentation'))
);

-- Indexes for performance
CREATE INDEX idx_content_chunks_file_id ON content_chunks(file_id);
CREATE INDEX idx_content_chunks_content_type ON content_chunks(content_type);
CREATE INDEX idx_content_chunks_created_at ON content_chunks(created_at);
CREATE INDEX idx_content_chunks_metadata ON content_chunks USING gin (metadata);

-- Partial indexes for type-specific queries
CREATE INDEX idx_content_chunks_code_dml ON content_chunks(file_id, chunk_number) WHERE content_type = 'code_dml';
CREATE INDEX idx_content_chunks_python ON content_chunks(file_id, chunk_number) WHERE content_type = 'python_test';
CREATE INDEX idx_content_chunks_docs ON content_chunks(file_id, chunk_number) WHERE content_type = 'documentation';

-- Vector similarity search index (if using pgvector)
CREATE INDEX idx_content_chunks_embedding ON content_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comments
COMMENT ON TABLE content_chunks IS 'File-based text chunks with embeddings for RAG operations';
COMMENT ON COLUMN content_chunks.file_id IS 'Reference to the source file in files table';
COMMENT ON COLUMN content_chunks.chunk_number IS 'Sequential number of this chunk within the file';
COMMENT ON COLUMN content_chunks.content_type IS 'Type of content: code_dml, python_test, or documentation';
COMMENT ON COLUMN content_chunks.summary IS 'LLM-generated summary (optional, NULL if not generated)';
COMMENT ON COLUMN content_chunks.metadata IS 'Additional metadata stored as JSONB (title, section, word_count, has_code, heading_hierarchy, language_hints, AST info, etc.)';
COMMENT ON COLUMN content_chunks.embedding IS 'Vector embedding for semantic similarity search';
