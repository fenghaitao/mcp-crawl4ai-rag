-- Delete all data for a specific source_id from crawled_pages table
-- This script maintains sync between the sources and crawled_pages tables
-- 
-- Usage:
--   1. Replace 'YOUR_SOURCE_ID' with the actual source_id you want to delete
--   2. Run this script in your PostgreSQL/Supabase SQL editor
--
-- Example source_ids:
--   - 'simics-dml'      : DML source files
--   - 'simics-python'   : Python source files  
--   - 'simics-cc'       : C/C++ source files
--   - 'simics-source'   : General source files
--   - 'doc'             : Documentation files

-- =============================================================================
-- CONFIGURATION: Set the source_id you want to delete
-- =============================================================================
DO $$
DECLARE
    target_source_id TEXT := 'YOUR_SOURCE_ID';  -- ⚠️  CHANGE THIS VALUE
    deleted_count INTEGER;
    total_word_count_val INTEGER;
BEGIN
    -- Start transaction
    RAISE NOTICE 'Starting deletion for source_id: %', target_source_id;
    
    -- Check if source exists
    IF NOT EXISTS (SELECT 1 FROM sources WHERE source_id = target_source_id) THEN
        RAISE EXCEPTION 'Source ID "%" does not exist in sources table', target_source_id;
    END IF;
    
    -- Get current count before deletion
    SELECT COUNT(*) INTO deleted_count 
    FROM crawled_pages 
    WHERE source_id = target_source_id;
    
    RAISE NOTICE 'Found % rows to delete for source_id: %', deleted_count, target_source_id;
    
    -- Delete all crawled_pages entries for this source_id
    DELETE FROM crawled_pages 
    WHERE source_id = target_source_id;
    
    RAISE NOTICE 'Deleted % rows from crawled_pages', deleted_count;
    
    -- Reset the word count in sources table to 0
    UPDATE sources 
    SET 
        total_word_count = 0,
        updated_at = timezone('utc'::text, now())
    WHERE source_id = target_source_id;
    
    -- Get the updated word count (should be 0)
    SELECT total_word_count INTO total_word_count_val 
    FROM sources 
    WHERE source_id = target_source_id;
    
    RAISE NOTICE 'Updated sources table: total_word_count = %', total_word_count_val;
    RAISE NOTICE 'Successfully deleted all data for source_id: %', target_source_id;
    RAISE NOTICE '✓ Deletion complete!';
END $$;

-- =============================================================================
-- Verification Query: Check the results
-- =============================================================================
-- Uncomment the following lines to verify the deletion:

-- SELECT 
--     s.source_id,
--     s.total_word_count,
--     COUNT(cp.id) as remaining_pages,
--     s.updated_at
-- FROM sources s
-- LEFT JOIN crawled_pages cp ON s.source_id = cp.source_id
-- WHERE s.source_id = 'YOUR_SOURCE_ID'  -- ⚠️  CHANGE THIS VALUE
-- GROUP BY s.source_id, s.total_word_count, s.updated_at;
