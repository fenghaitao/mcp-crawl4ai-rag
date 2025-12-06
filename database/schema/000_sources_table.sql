-- Create the sources table that other tables reference
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    summary TEXT,
    total_word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Add some comments
COMMENT ON TABLE sources IS 'High-level source collections (e.g., simics-dml, simics-python)';
COMMENT ON COLUMN sources.source_id IS 'Unique identifier for the source';
COMMENT ON COLUMN sources.summary IS 'Summary description of the source';
COMMENT ON COLUMN sources.total_word_count IS 'Total word count across all files in this source';