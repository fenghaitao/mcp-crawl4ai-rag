-- Create a stored function to delete all data for a specific source_id
-- This function maintains sync between the sources and crawled_pages tables
--
-- Usage:
--   SELECT delete_source_data('simics-dml');
--   SELECT delete_source_data('simics-python');
--
-- The function will:
--   1. Delete all crawled_pages entries for the given source_id
--   2. Reset the total_word_count to 0 in the sources table
--   3. Update the updated_at timestamp
--   4. Return a summary of what was deleted

-- =============================================================================
-- Create the function
-- =============================================================================
CREATE OR REPLACE FUNCTION delete_source_data(target_source_id TEXT)
RETURNS TABLE(
    source_id TEXT,
    deleted_pages INTEGER,
    previous_word_count INTEGER,
    status TEXT
) AS $$
DECLARE
    deleted_count INTEGER;
    previous_count INTEGER;
BEGIN
    -- Check if source exists
    IF NOT EXISTS (SELECT 1 FROM sources WHERE sources.source_id = target_source_id) THEN
        RAISE EXCEPTION 'Source ID "%" does not exist in sources table', target_source_id;
    END IF;
    
    -- Get current word count before deletion
    SELECT total_word_count INTO previous_count
    FROM sources 
    WHERE sources.source_id = target_source_id;
    
    -- Count pages to be deleted
    SELECT COUNT(*) INTO deleted_count 
    FROM crawled_pages 
    WHERE crawled_pages.source_id = target_source_id;
    
    -- Delete all crawled_pages entries for this source_id
    DELETE FROM crawled_pages 
    WHERE crawled_pages.source_id = target_source_id;
    
    -- Reset the word count in sources table to 0
    UPDATE sources 
    SET 
        total_word_count = 0,
        updated_at = timezone('utc'::text, now())
    WHERE sources.source_id = target_source_id;
    
    -- Return summary
    RETURN QUERY
    SELECT 
        target_source_id,
        deleted_count,
        previous_count,
        'Successfully deleted ' || deleted_count || ' pages and reset word count from ' || previous_count || ' to 0'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Example Usage
-- =============================================================================

-- Delete all DML source files:
-- SELECT * FROM delete_source_data('simics-dml');

-- Delete all Python source files:
-- SELECT * FROM delete_source_data('simics-python');

-- Delete all C/C++ source files:
-- SELECT * FROM delete_source_data('simics-cc');

-- Delete all documentation files:
-- SELECT * FROM delete_source_data('doc');

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- Check all sources and their page counts:
-- SELECT 
--     s.source_id,
--     s.total_word_count,
--     COUNT(cp.id) as page_count,
--     s.updated_at
-- FROM sources s
-- LEFT JOIN crawled_pages cp ON s.source_id = cp.source_id
-- GROUP BY s.source_id, s.total_word_count, s.updated_at
-- ORDER BY s.source_id;
