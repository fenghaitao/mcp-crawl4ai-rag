# Design Document: Hybrid Search with BM25 Sparse Indexing

## Overview

This design document describes the implementation of hybrid search functionality in the ChromaDB backend. The system will combine dense vector embeddings (semantic search) with sparse BM25 indexing (keyword search) to provide more accurate and comprehensive search results. The implementation leverages ChromaDB's native support for sparse vectors and BM25 embedding functions, introduced in recent versions of the library.

The hybrid search approach addresses limitations of pure semantic search (missing exact keyword matches) and pure keyword search (missing semantic relationships) by combining both methods and using Reciprocal Rank Fusion (RRF) to merge results intelligently.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Query Interface                           │
│              semantic_search(query_text, ...)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Hybrid Search Check  │
         │  (USE_HYBRID_SEARCH)  │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│  Dense Search   │    │  Sparse Search  │
│  (Embeddings)   │    │     (BM25)      │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌─────────────────────┐
         │   Result Merging    │
         │       (RRF)         │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │    Re-ranking       │
         │  (Score + Filter)   │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────────┐
         │  Return Results     │
         └─────────────────────┘
```

### Component Interaction

1. **Configuration Layer**: Reads `USE_HYBRID_SEARCH` environment variable to determine search mode
2. **Collection Initialization**: Sets up ChromaDB collection with BM25 schema when hybrid search is enabled
3. **Search Execution**: Performs parallel dense and sparse searches when hybrid mode is active
4. **Result Fusion**: Merges results using RRF algorithm
5. **Post-processing**: Applies re-ranking, filtering, and limiting

## Components and Interfaces

### 1. ChromaBackend Class Extensions

#### New Methods

```python
def _is_hybrid_search_enabled(self) -> bool:
    """Check if hybrid search is enabled via environment variable."""
    
def _setup_hybrid_collection(self, collection_name: str):
    """Set up collection with BM25 sparse indexing support."""
    
def _perform_dense_search(self, query_embedding: List[float], 
                         limit: int, where_clause: Optional[Dict]) -> List[Dict]:
    """Perform dense vector search."""
    
def _perform_sparse_search(self, query_text: str, 
                          limit: int, where_clause: Optional[Dict]) -> List[Dict]:
    """Perform BM25 sparse search."""
    
def _merge_results_with_rrf(self, dense_results: List[Dict], 
                            sparse_results: List[Dict], k: int = 60) -> List[Dict]:
    """Merge search results using Reciprocal Rank Fusion."""
```

#### Modified Methods

```python
def _get_or_create_metadata_collection(self, name: str):
    """Enhanced to support hybrid search schema for content_chunks collection."""
    
def semantic_search(self, query_text: str, limit: int = 5,
                   content_type: Optional[str] = None,
                   threshold: Optional[float] = None) -> List[Dict[str, Any]]:
    """Enhanced to support hybrid search when enabled."""
```

### 2. BM25 Integration

ChromaDB provides native BM25 support through:

```python
from chromadb import Schema, K
from chromadb.utils.embedding_functions import Bm25EmbeddingFunction

# Initialize BM25 embedding function
bm25_ef = Bm25EmbeddingFunction()

# Define schema with sparse index
schema = Schema()
schema.create_index(
    key='bm25_sparse_vector',
    config={
        'embedding_function': bm25_ef,
        'source_key': K.DOCUMENT
    }
)

# Create collection with schema
collection = client.get_or_create_collection(
    name="content_chunks",
    schema=schema
)
```

### 3. Search API Interface

The `semantic_search` method maintains its existing signature:

```python
def semantic_search(
    self, 
    query_text: str,           # Query string
    limit: int = 5,            # Maximum results to return
    content_type: Optional[str] = None,  # Filter by content type
    threshold: Optional[float] = None    # Minimum similarity threshold
) -> List[Dict[str, Any]]:
    """
    Returns list of dictionaries with:
    - id: Chunk ID
    - content: Chunk text
    - metadata: Chunk metadata
    - similarity: Cosine similarity score (0-1)
    - rrf_score: RRF score (only in hybrid mode)
    - url: Source URL
    - chunk_number: Position in document
    - summary: Chunk summary
    - file_id: Associated file ID
    """
```

## Data Models

### Collection Schema

#### Content Chunks Collection (with Hybrid Search)

```python
{
    "name": "content_chunks",
    "schema": {
        "indexes": [
            {
                "key": "bm25_sparse_vector",
                "type": "sparse",
                "config": {
                    "embedding_function": Bm25EmbeddingFunction(),
                    "source_key": K.DOCUMENT
                }
            }
        ]
    },
    "metadata": {
        "hnsw:space": "cosine"  # For dense vectors
    }
}
```

### Result Data Model

```python
{
    "id": str,                    # Chunk identifier
    "content": str,               # Chunk text content
    "metadata": {                 # Chunk metadata
        "file_id": str,
        "url": str,
        "chunk_number": int,
        "content_type": str,
        "summary": str,
        "title": str,
        "section": str,
        "word_count": int,
        # ... other metadata fields
    },
    "similarity": float,          # Cosine similarity (0-1)
    "distance": float,            # L2 distance
    "rrf_score": float,          # RRF score (hybrid mode only)
    "dense_rank": int,           # Rank in dense results (hybrid mode only)
    "sparse_rank": int,          # Rank in sparse results (hybrid mode only)
    "url": str,                  # Convenience field
    "chunk_number": int,         # Convenience field
    "summary": str,              # Convenience field
    "file_id": str               # Convenience field
}
```

### RRF Algorithm

Reciprocal Rank Fusion (RRF) combines rankings from multiple retrieval systems:

```
For each document d:
    RRF_score(d) = Σ (1 / (k + rank_i(d)))
    
Where:
    - k is a constant (typically 60)
    - rank_i(d) is the rank of document d in retrieval system i
    - Σ sums over all retrieval systems where d appears
```

Example:
- Document appears at rank 1 in dense search: 1/(60+1) = 0.0164
- Document appears at rank 3 in sparse search: 1/(60+3) = 0.0159
- Combined RRF score: 0.0164 + 0.0159 = 0.0323

## Correctness Properties


*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dual vector generation for all documents
*For any* document added to a hybrid-enabled collection, both dense embeddings and sparse BM25 vectors should be generated and stored
**Validates: Requirements 1.3**

### Property 2: Configuration value interpretation
*For any* environment variable value in the set {"true", "1", "yes"} (case-insensitive), the system should enable hybrid search mode
**Validates: Requirements 2.1**

### Property 3: Default to dense-only for invalid configuration
*For any* environment variable value that is not in {"true", "1", "yes"}, including empty or missing values, the system should default to dense-only search mode
**Validates: Requirements 2.4**

### Property 4: Dual search execution in hybrid mode
*For any* query executed with hybrid search enabled, both dense vector search and BM25 sparse search should be performed
**Validates: Requirements 3.1, 3.2**

### Property 5: Graceful degradation on partial failure
*For any* search operation where one method fails, the system should return results from the successful method and log the failure
**Validates: Requirements 3.5, 8.5**

### Property 6: RRF formula correctness
*For any* document with known ranks in dense and sparse results, the RRF score should equal sum(1 / (60 + rank_i)) across all retrieval methods where the document appears
**Validates: Requirements 4.2, 4.3, 4.4**

### Property 7: RRF score ordering
*For any* merged result set from RRF, the results should be sorted in descending order by RRF score
**Validates: Requirements 4.5, 5.1**

### Property 8: Result limit enforcement
*For any* limit parameter value n, the returned results should contain at most n items
**Validates: Requirements 5.2**

### Property 9: Threshold filtering
*For any* threshold value t, all returned results should have similarity scores greater than or equal to t
**Validates: Requirements 5.3**

### Property 10: Result structure completeness
*For any* result returned in hybrid mode, the result should contain both the original similarity score and the RRF score fields
**Validates: Requirements 5.4**

### Property 11: Backward compatible result structure
*For any* result returned, all original fields (id, content, metadata, similarity, url, chunk_number, summary, file_id) should be present
**Validates: Requirements 6.3**

### Property 12: Content type filter application
*For any* content_type filter specified, all returned results should have metadata.content_type matching the filter value
**Validates: Requirements 6.4**

## Error Handling

### Error Categories

1. **Configuration Errors**
   - Invalid ChromaDB version (no BM25 support)
   - Missing or invalid environment variables
   - Collection initialization failures

2. **Runtime Errors**
   - Embedding generation failures
   - BM25 indexing failures
   - Search execution failures
   - Result merging errors

3. **Input Validation Errors**
   - Empty or whitespace-only queries
   - Invalid limit parameters (< 1)
   - Invalid threshold values

### Error Handling Strategy

```python
def semantic_search(self, query_text: str, limit: int = 5, ...) -> List[Dict]:
    try:
        # Input validation
        if not query_text or query_text.strip() == '':
            logger.warning("Empty query text provided")
            return []
        
        if limit < 1:
            logger.warning(f"Invalid limit {limit}, using default 5")
            limit = 5
        
        # Check hybrid search mode
        if not self._is_hybrid_search_enabled():
            return self._perform_dense_only_search(...)
        
        # Attempt hybrid search with fallback
        try:
            dense_results = self._perform_dense_search(...)
        except Exception as e:
            logger.error(f"Dense search failed: {e}", exc_info=True)
            dense_results = []
        
        try:
            sparse_results = self._perform_sparse_search(...)
        except Exception as e:
            logger.error(f"Sparse search failed: {e}", exc_info=True)
            sparse_results = []
        
        # If both failed, return empty
        if not dense_results and not sparse_results:
            logger.error("Both search methods failed")
            return []
        
        # If only one succeeded, return those results
        if not dense_results:
            logger.warning("Using sparse-only results")
            return sparse_results[:limit]
        
        if not sparse_results:
            logger.warning("Using dense-only results")
            return dense_results[:limit]
        
        # Merge results with RRF
        merged_results = self._merge_results_with_rrf(dense_results, sparse_results)
        
        # Apply threshold and limit
        filtered_results = self._apply_threshold_and_limit(merged_results, threshold, limit)
        
        return filtered_results
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        return []
```

### Fallback Behavior

1. **BM25 Not Available**: Fall back to dense-only search
2. **Embedding Generation Fails**: Attempt BM25-only search
3. **One Search Method Fails**: Use results from successful method
4. **Both Methods Fail**: Return empty list with error logging
5. **Collection Not Found**: Create collection with appropriate schema

## Testing Strategy

### Unit Testing

Unit tests will verify specific behaviors and edge cases:

1. **Configuration Tests**
   - Test environment variable parsing for all valid values
   - Test default behavior with missing/invalid values
   - Test `_is_hybrid_search_enabled()` method

2. **Collection Setup Tests**
   - Test collection creation with BM25 schema
   - Test fallback when BM25 is not available
   - Test schema validation

3. **Search Method Tests**
   - Test dense-only search when hybrid is disabled
   - Test dual search execution when hybrid is enabled
   - Test individual search methods (`_perform_dense_search`, `_perform_sparse_search`)

4. **RRF Algorithm Tests**
   - Test RRF calculation with known inputs
   - Test score combination for documents in both result sets
   - Test score calculation for documents in single result set
   - Test result ordering by RRF score

5. **Error Handling Tests**
   - Test empty query handling
   - Test invalid limit handling
   - Test search method failure scenarios
   - Test embedding generation failure

6. **Filtering Tests**
   - Test content_type filtering
   - Test threshold filtering
   - Test limit enforcement

### Property-Based Testing

Property-based tests will verify universal properties across many random inputs using the Hypothesis library for Python:

1. **Configuration Property Tests**
   - Generate random environment variable values
   - Verify correct interpretation of valid values
   - Verify default behavior for invalid values

2. **Search Execution Property Tests**
   - Generate random queries
   - Verify dual search execution in hybrid mode
   - Verify result structure completeness

3. **RRF Algorithm Property Tests**
   - Generate random result sets with rankings
   - Verify RRF formula correctness
   - Verify score ordering invariant

4. **Filtering Property Tests**
   - Generate random limit values
   - Verify result count never exceeds limit
   - Generate random threshold values
   - Verify all results meet threshold

5. **Backward Compatibility Property Tests**
   - Generate random queries
   - Verify result structure contains all original fields
   - Verify content_type filter application

### Integration Testing

Integration tests will verify end-to-end functionality:

1. **Full Hybrid Search Flow**
   - Ingest documents with both vector types
   - Execute hybrid search queries
   - Verify merged results are correct

2. **Backward Compatibility**
   - Run existing tests with hybrid search disabled
   - Verify no regressions in dense-only mode

3. **Performance Testing**
   - Compare hybrid search vs dense-only performance
   - Measure RRF merging overhead
   - Test with large result sets

### Test Configuration

- Property-based tests should run a minimum of 100 iterations per property
- Each property-based test must include a comment referencing the design document property
- Comment format: `# Feature: hybrid-search, Property {number}: {property_text}`

## Implementation Notes

### ChromaDB Version Requirements

Hybrid search with BM25 requires ChromaDB version 0.5.0 or later. The implementation should:

1. Check ChromaDB version at initialization
2. Log a warning if version is too old
3. Automatically disable hybrid search if BM25 is not available

### Performance Considerations

1. **Result Set Sizing**: Request 2x the limit from each search method to ensure sufficient candidates for RRF merging
2. **Parallel Execution**: Consider executing dense and sparse searches in parallel for better performance
3. **Caching**: Consider caching BM25 embedding function to avoid re-initialization
4. **Logging Overhead**: Use appropriate log levels to minimize performance impact in production

### Migration Path

For existing deployments:

1. Hybrid search is opt-in via environment variable
2. Existing collections continue to work without modification
3. New collections created with hybrid search enabled will have BM25 indexing
4. Existing collections can be migrated by:
   - Enabling hybrid search
   - Deleting and recreating the collection
   - Re-ingesting documents

### Configuration Example

```bash
# Enable hybrid search
export USE_HYBRID_SEARCH=true

# Or in .env file
USE_HYBRID_SEARCH=true
```

## Dependencies

### New Dependencies

- ChromaDB >= 0.5.0 (for BM25 support)
- No additional Python packages required (BM25 is built into ChromaDB)

### Existing Dependencies

- chromadb (existing)
- numpy (existing, for embedding handling)
- logging (standard library)
- os (standard library)

## Deployment Considerations

1. **Environment Variable**: Set `USE_HYBRID_SEARCH=true` to enable hybrid search
2. **Collection Migration**: Existing collections need to be recreated to support BM25
3. **Backward Compatibility**: System works without changes when hybrid search is disabled
4. **Monitoring**: Add logging to track hybrid search usage and performance
5. **Rollback**: Can disable hybrid search by removing/changing environment variable

## Future Enhancements

1. **Configurable RRF Constant**: Allow k parameter to be configured via environment variable
2. **Custom Weighting**: Allow different weights for dense vs sparse results
3. **Query Expansion**: Add query expansion techniques for better recall
4. **Result Caching**: Cache frequent queries to improve performance
5. **A/B Testing**: Add metrics to compare hybrid vs dense-only search quality
