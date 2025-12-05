-- Migration: Add user-documentation source
-- This migration ensures the 'user-documentation' source exists for user manual chunks

-- Insert user-documentation source if it doesn't exist
INSERT INTO sources (source_id, summary, total_word_count) VALUES
    ('user-documentation', 'User manual and technical documentation files', 0)
ON CONFLICT (source_id) DO NOTHING;

-- Add comment
COMMENT ON TABLE sources IS 
'Source metadata table. Each source represents a collection of related documents (e.g., DML source code, Python source code, user documentation).';
