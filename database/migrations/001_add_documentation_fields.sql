-- Migration: Add fields to support user manual documentation
-- This migration adds content_type field and heading_hierarchy indexing
-- to distinguish documentation from code and enable hierarchical retrieval

-- Add content_type field to crawled_pages table
-- This field distinguishes between 'code', 'documentation', and 'mixed' content
ALTER TABLE crawled_pages 
ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'code';

-- Add comment to explain the field
COMMENT ON COLUMN crawled_pages.content_type IS 
'Content type: code (source code), documentation (user manuals), or mixed';

-- Add heading_hierarchy field to store document structure
-- This is stored as JSONB for flexible querying
ALTER TABLE crawled_pages
ADD COLUMN IF NOT EXISTS heading_hierarchy JSONB DEFAULT '[]'::jsonb;

-- Add comment to explain the field
COMMENT ON COLUMN crawled_pages.heading_hierarchy IS 
'Hierarchical heading path as JSON array, e.g., ["User Guide", "Installation", "Prerequisites"]';

-- Create index on content_type for efficient filtering
CREATE INDEX IF NOT EXISTS idx_crawled_pages_content_type 
ON crawled_pages(content_type);

-- Create GIN index on heading_hierarchy for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_crawled_pages_heading_hierarchy 
ON crawled_pages USING GIN (heading_hierarchy);

-- Add content_type to code_examples table as well
ALTER TABLE code_examples
ADD COLUMN IF NOT EXISTS content_type TEXT DEFAULT 'code';

COMMENT ON COLUMN code_examples.content_type IS 
'Content type: code (source code examples) or documentation (documentation code examples)';

-- Create index on content_type for code_examples
CREATE INDEX IF NOT EXISTS idx_code_examples_content_type 
ON code_examples(content_type);

-- Update existing records to have 'code' as default content_type
-- (This is safe since all existing records are code)
UPDATE crawled_pages 
SET content_type = 'code' 
WHERE content_type IS NULL;

UPDATE code_examples 
SET content_type = 'code' 
WHERE content_type IS NULL;

-- Add check constraint to ensure valid content_type values
ALTER TABLE crawled_pages
ADD CONSTRAINT check_content_type 
CHECK (content_type IN ('code', 'documentation', 'mixed'));

ALTER TABLE code_examples
ADD CONSTRAINT check_code_examples_content_type 
CHECK (content_type IN ('code', 'documentation'));
