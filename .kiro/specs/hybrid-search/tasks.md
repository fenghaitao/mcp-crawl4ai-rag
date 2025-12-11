# Implementation Plan

- [x] 1. Add hybrid search configuration support
  - Add `_is_hybrid_search_enabled()` method to check USE_HYBRID_SEARCH environment variable
  - Method should return True for values "true", "1", "yes" (case-insensitive), False otherwise
  - _Requirements: 2.1, 2.4, 2.5_

- [ ]* 1.1 Write property test for configuration value interpretation
  - **Property 2: Configuration value interpretation**
  - **Validates: Requirements 2.1**

- [ ]* 1.2 Write property test for default configuration behavior
  - **Property 3: Default to dense-only for invalid configuration**
  - **Validates: Requirements 2.4**

- [x] 2. Implement BM25 collection setup
  - Create `_setup_hybrid_collection()` method to configure ChromaDB collection with BM25 schema
  - Use `chromadb.Schema()` and `Bm25EmbeddingFunction()` to create sparse index
  - Configure index with key='bm25_sparse_vector' and source_key=K.DOCUMENT
  - Add error handling to fall back to dense-only if BM25 is not available
  - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [ ]* 2.1 Write property test for dual vector generation
  - **Property 1: Dual vector generation for all documents**
  - **Validates: Requirements 1.3**

- [x] 3. Modify collection initialization to support hybrid search
  - Update `_get_or_create_metadata_collection()` to check if collection is 'content_chunks'
  - If hybrid search is enabled and collection is 'content_chunks', call `_setup_hybrid_collection()`
  - Otherwise, use existing collection creation logic
  - Add logging for hybrid search configuration status
  - _Requirements: 1.4, 7.1_

- [x] 4. Implement dense search method
  - Create `_perform_dense_search()` method that performs vector embedding search
  - Accept parameters: query_embedding, limit, where_clause
  - Use ChromaDB's query() method with query_embeddings parameter
  - Return list of results with similarity scores
  - Add error handling and logging
  - _Requirements: 3.1_

- [x] 5. Implement sparse search method
  - Create `_perform_sparse_search()` method that performs BM25 search
  - Accept parameters: query_text, limit, where_clause
  - Use ChromaDB's search API with BM25 sparse vectors
  - Return list of results with BM25 scores
  - Add error handling and logging
  - _Requirements: 3.2_

- [x] 6. Implement RRF merging algorithm
  - Create `_merge_results_with_rrf()` method to merge dense and sparse results
  - Accept parameters: dense_results, sparse_results, k (default 60)
  - Calculate RRF score for each document: sum(1 / (k + rank)) across all methods
  - Combine scores for documents appearing in both result sets
  - Sort merged results by RRF score in descending order
  - Add RRF score, dense_rank, and sparse_rank to result metadata
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 6.1 Write property test for RRF formula correctness
  - **Property 6: RRF formula correctness**
  - **Validates: Requirements 4.2, 4.3, 4.4**

- [ ]* 6.2 Write property test for RRF score ordering
  - **Property 7: RRF score ordering**
  - **Validates: Requirements 4.5, 5.1**

- [x] 7. Implement result filtering and limiting
  - Create `_apply_threshold_and_limit()` method
  - Filter results by similarity threshold if specified
  - Limit results to requested limit parameter
  - Ensure all results contain required fields (similarity, rrf_score in hybrid mode)
  - _Requirements: 5.2, 5.3, 5.4_

- [ ]* 7.1 Write property test for result limit enforcement
  - **Property 8: Result limit enforcement**
  - **Validates: Requirements 5.2**

- [ ]* 7.2 Write property test for threshold filtering
  - **Property 9: Threshold filtering**
  - **Validates: Requirements 5.3**

- [ ]* 7.3 Write property test for result structure completeness
  - **Property 10: Result structure completeness**
  - **Validates: Requirements 5.4**

- [x] 8. Update semantic_search method for hybrid search
  - Add input validation (empty query, invalid limit)
  - Check if hybrid search is enabled using `_is_hybrid_search_enabled()`
  - If disabled, use existing dense-only implementation
  - If enabled, perform both dense and sparse searches
  - Request 2x limit from each method to ensure sufficient candidates
  - Handle partial failures (one method fails, use other method's results)
  - Merge results using `_merge_results_with_rrf()`
  - Apply filtering and limiting
  - Add comprehensive logging for all steps
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.2, 7.3, 7.4, 7.5, 8.1, 8.4, 8.5_

- [ ]* 8.1 Write property test for dual search execution
  - **Property 4: Dual search execution in hybrid mode**
  - **Validates: Requirements 3.1, 3.2**

- [ ]* 8.2 Write property test for graceful degradation
  - **Property 5: Graceful degradation on partial failure**
  - **Validates: Requirements 3.5, 8.5**

- [ ]* 8.3 Write property test for backward compatible result structure
  - **Property 11: Backward compatible result structure**
  - **Validates: Requirements 6.3**

- [ ]* 8.4 Write property test for content type filter application
  - **Property 12: Content type filter application**
  - **Validates: Requirements 6.4**

- [x] 9. Add backward compatibility safeguards
  - Ensure semantic_search maintains same method signature
  - Ensure result structure includes all original fields
  - Add fallback to dense-only when BM25 is not configured
  - Test that existing code works without modifications when hybrid search is disabled
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 11. Add integration tests for hybrid search
  - Test full hybrid search flow with document ingestion
  - Test backward compatibility with hybrid search disabled
  - Test performance comparison between hybrid and dense-only
  - Test edge cases (empty queries, invalid parameters, missing collections)
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 12. Update documentation
  - Add hybrid search configuration to README
  - Document USE_HYBRID_SEARCH environment variable
  - Add examples of hybrid search usage
  - Document migration path for existing deployments
  - Add troubleshooting guide for common issues
