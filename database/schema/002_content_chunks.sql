-- Fresh content_chunks table for new file-based RAG operations
-- This is a separate table from the existing crawled_pages table

CREATE TABLE content_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL,                           -- Reference to files table
    url VARCHAR NOT NULL,                              -- URL or file path for this chunk
    chunk_number INTEGER NOT NULL,                     -- Sequential number of this chunk within the file
    content TEXT NOT NULL,                             -- The actual text content of the chunk
    content_type VARCHAR(50) NOT NULL,                 -- 'code_dml', 'python_test', 'documentation'
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,       -- Additional metadata as JSON
    source_id TEXT NOT NULL,                           -- Reference to sources table
    embedding vector(1536),                            -- Vector embedding for semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE,
    UNIQUE(file_id, chunk_number),                     -- Prevent duplicate chunks per file
    CHECK (chunk_number >= 0),
    CHECK (content_type IN ('code_dml', 'python_test', 'documentation'))
);

-- Indexes for performance
CREATE INDEX idx_content_chunks_file_id ON content_chunks(file_id);
CREATE INDEX idx_content_chunks_source_id ON content_chunks(source_id);
CREATE INDEX idx_content_chunks_content_type ON content_chunks(content_type);
CREATE INDEX idx_content_chunks_created_at ON content_chunks(created_at);

-- Partial indexes for type-specific queries
CREATE INDEX idx_content_chunks_code_dml ON content_chunks(file_id, chunk_number) WHERE content_type = 'code_dml';
CREATE INDEX idx_content_chunks_python ON content_chunks(file_id, chunk_number) WHERE content_type = 'python_test';
CREATE INDEX idx_content_chunks_docs ON content_chunks(file_id, chunk_number) WHERE content_type = 'documentation';

-- Vector similarity search index (if using pgvector)
CREATE INDEX idx_content_chunks_embedding ON content_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comments
COMMENT ON TABLE content_chunks IS 'New file-based text chunks with embeddings for RAG operations';
COMMENT ON COLUMN content_chunks.file_id IS 'Reference to the source file in files table';
COMMENT ON COLUMN content_chunks.chunk_number IS 'Sequential number of this chunk within the file';
COMMENT ON COLUMN content_chunks.content_type IS 'Type of content: code_dml, python_test, or documentation';
COMMENT ON COLUMN content_chunks.metadata IS 'Additional metadata stored as JSONB';
COMMENT ON COLUMN content_chunks.embedding IS 'Vector embedding for semantic similarity search';
