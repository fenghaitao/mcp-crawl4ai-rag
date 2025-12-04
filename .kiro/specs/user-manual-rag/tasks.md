# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create `src/user_manual_chunker/` directory structure
  - Define abstract base classes for DocumentParser, SemanticChunker, MetadataExtractor
  - Define data models (DocumentStructure, Heading, CodeBlock, Paragraph, ChunkMetadata, ProcessedChunk)
  - Set up configuration management for chunk sizes and model selection
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ]* 1.1 Write unit tests for data models
  - Test DocumentStructure creation and section extraction
  - Test Heading hierarchy building
  - Test CodeBlock and Paragraph creation
  - Test ChunkMetadata serialization
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 2. Implement markdown parser
  - [x] 2.1 Create MarkdownParser class implementing DocumentParser interface
    - Parse headings with regex and markdown library
    - Extract code blocks (triple-backtick and indented formats)
    - Extract paragraphs and inline code
    - Build heading hierarchy with parent relationships
    - _Requirements: 1.1, 5.1, 5.3, 5.4_

  - [ ]* 2.2 Write property test for markdown parsing completeness
    - **Property 1: Document structure parsing completeness**
    - **Validates: Requirements 1.1, 5.1**

  - [ ]* 2.3 Write property test for code block format recognition
    - **Property 15: Code block format recognition**
    - **Validates: Requirements 5.3**

  - [ ]* 2.4 Write property test for inline code preservation
    - **Property 16: Inline code marker preservation**
    - **Validates: Requirements 5.4**

  - [ ]* 2.5 Write unit tests for markdown parser edge cases
    - Test malformed markdown
    - Test empty documents
    - Test documents with only code blocks
    - Test nested list structures
    - _Requirements: 1.1, 5.1_

- [x] 3. Implement HTML parser
  - [x] 3.1 Create HTMLParser class implementing DocumentParser interface
    - Parse HTML with BeautifulSoup
    - Extract headings from h1-h6 tags
    - Extract code blocks from pre/code tags
    - Extract paragraphs from p tags
    - Preserve structural hierarchy
    - _Requirements: 5.2_

  - [ ]* 3.2 Write property test for HTML structure preservation
    - **Property 14: HTML structure preservation**
    - **Validates: Requirements 5.2**

  - [ ]* 3.3 Write unit tests for HTML parser
    - Test simple HTML document
    - Test nested HTML structure
    - Test HTML with inline styles
    - Test malformed HTML
    - _Requirements: 5.2_

- [x] 4. Implement semantic chunker
  - [x] 4.1 Create SemanticChunker class with configurable parameters
    - Initialize with max_chunk_size, min_chunk_size, chunk_overlap, size_metric
    - Implement size calculation (characters or tokens)
    - Implement section-level chunking logic
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 4.2 Implement code block integrity preservation
    - Detect code blocks within sections
    - Keep code blocks with preceding explanatory text
    - Never split code blocks across chunks
    - _Requirements: 1.2, 1.4_

  - [ ]* 4.3 Write property test for code block integrity
    - **Property 2: Code block integrity preservation**
    - **Validates: Requirements 1.2, 1.4**

  - [x] 4.4 Implement section splitting at paragraph boundaries
    - Split large sections at paragraph boundaries
    - Ensure no sentence splitting
    - Include section heading in each split chunk
    - _Requirements: 1.3, 1.5, 6.3_

  - [ ]* 4.5 Write property test for paragraph boundary splitting
    - **Property 3: Section splitting at paragraph boundaries**
    - **Validates: Requirements 1.3, 6.3**

  - [ ]* 4.6 Write property test for heading preservation in splits
    - **Property 4: Heading context preservation in splits**
    - **Validates: Requirements 1.5, 6.1**

  - [x] 4.7 Implement small section merging
    - Merge sections smaller than min_chunk_size
    - Respect semantic boundaries when merging
    - _Requirements: 4.4_

  - [ ]* 4.8 Write property test for small section merging
    - **Property 12: Small section merging**
    - **Validates: Requirements 4.4**

  - [x] 4.9 Implement chunk overlap
    - Create overlapping regions between adjacent chunks
    - Ensure overlap includes complete sentences
    - _Requirements: 4.5, 6.2_

  - [ ]* 4.10 Write property test for chunk overlap
    - **Property 13: Chunk overlap correctness**
    - **Validates: Requirements 4.5, 6.2**

  - [ ]* 4.11 Write unit tests for semantic chunker
    - Test single-chunk document
    - Test multi-chunk document
    - Test document with only code
    - Test empty document handling
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 5. Implement special pattern handlers
  - [x] 5.1 Implement list context preservation
    - Keep list items with parent context
    - Handle nested lists
    - _Requirements: 5.5_

  - [ ]* 5.2 Write property test for list preservation
    - **Property 17: List item context preservation**
    - **Validates: Requirements 5.5**

  - [x] 5.3 Implement API documentation pattern handler
    - Keep function signatures with descriptions
    - Detect API documentation patterns
    - _Requirements: 9.1_

  - [ ]* 5.4 Write property test for API documentation
    - **Property 24: API documentation pattern preservation**
    - **Validates: Requirements 9.1**

  - [x] 5.5 Implement grammar specification handler
    - Keep grammar rules with examples
    - Detect grammar specification patterns
    - _Requirements: 9.2_

  - [ ]* 5.6 Write property test for grammar specifications
    - **Property 25: Grammar rule and example cohesion**
    - **Validates: Requirements 9.2**

  - [x] 5.7 Implement definition list handler
    - Keep terms with definitions
    - Handle various definition list formats
    - _Requirements: 9.3_

  - [ ]* 5.8 Write property test for definition lists
    - **Property 26: Definition list cohesion**
    - **Validates: Requirements 9.3**

  - [x] 5.9 Implement table preservation
    - Preserve table structure in chunk text
    - Handle markdown and HTML tables
    - _Requirements: 9.4_

  - [ ]* 5.10 Write property test for table preservation
    - **Property 27: Table structure preservation**
    - **Validates: Requirements 9.4**

  - [x] 5.11 Implement cross-reference preservation
    - Preserve reference links in chunks
    - Handle markdown and HTML links
    - _Requirements: 9.5_

  - [ ]* 5.12 Write property test for cross-reference preservation
    - **Property 28: Cross-reference link preservation**
    - **Validates: Requirements 9.5**

- [ ] 6. Checkpoint - Ensure all parsing and chunking tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement metadata extractor
  - [x] 7.1 Create MetadataExtractor class
    - Extract heading hierarchy for chunks
    - Record source file path
    - Detect code languages
    - Set contains_code flag
    - Calculate section level
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 7.2 Write property test for heading hierarchy extraction
    - **Property 5: Heading hierarchy extraction**
    - **Validates: Requirements 2.1, 6.5**

  - [ ]* 7.3 Write property test for source file metadata
    - **Property 6: Source file metadata presence**
    - **Validates: Requirements 2.2**

  - [ ]* 7.4 Write property test for code language detection
    - **Property 7: Code language detection**
    - **Validates: Requirements 2.3**

  - [ ]* 7.5 Write property test for code presence flag
    - **Property 8: Code presence flag accuracy**
    - **Validates: Requirements 2.4**

  - [ ]* 7.6 Write property test for section level accuracy
    - **Property 9: Section level accuracy**
    - **Validates: Requirements 2.5**

  - [ ]* 7.7 Write unit tests for metadata extractor
    - Test flat hierarchy extraction
    - Test nested hierarchy extraction
    - Test code language detection for various languages
    - Test missing metadata handling
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 8. Implement summary generator
  - [x] 8.1 Create SummaryGenerator class
    - Integrate with iflow_client for LLM-based summaries
    - Implement documentation-specific prompts
    - Add fallback extractive summary logic
    - Enforce summary length limits
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ]* 8.2 Write property test for summary generation
    - **Property 18: Summary generation completeness**
    - **Validates: Requirements 7.1**

  - [ ]* 8.3 Write property test for code mention in summaries
    - **Property 19: Code mention in summaries**
    - **Validates: Requirements 7.2**

  - [ ]* 8.4 Write property test for summary length constraint
    - **Property 20: Summary length constraint**
    - **Validates: Requirements 7.5**

  - [ ]* 8.5 Write unit tests for summary generator
    - Test LLM-based summary generation
    - Test fallback summary extraction
    - Test summary for code-heavy chunks
    - Test timeout handling
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [x] 9. Implement embedding generator
  - [x] 9.1 Create EmbeddingGenerator class
    - Integrate with existing embedding infrastructure
    - Implement batch processing
    - Preserve code syntax in embedding input
    - Normalize vectors for cosine similarity
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 9.2 Write property test for code syntax preservation
    - **Property 10: Code syntax preservation in embeddings**
    - **Validates: Requirements 3.2**

  - [ ]* 9.3 Write property test for vector normalization
    - **Property 11: Embedding vector normalization**
    - **Validates: Requirements 3.3**

  - [ ]* 9.4 Write unit tests for embedding generator
    - Test single chunk embedding
    - Test batch embedding
    - Test API failure handling
    - Test rate limiting
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 10. Implement main orchestrator
  - [x] 10.1 Create UserManualChunker class
    - Coordinate parsing, chunking, metadata extraction, summary, and embedding
    - Implement process_document method
    - Implement process_directory method
    - Generate unique chunk IDs
    - Track processing statistics
    - _Requirements: 8.1, 8.2, 8.5_

  - [ ]* 10.2 Write property test for output format
    - **Property 21: Output format completeness**
    - **Validates: Requirements 8.1**

  - [ ]* 10.3 Write property test for chunk ID uniqueness
    - **Property 22: Chunk ID uniqueness**
    - **Validates: Requirements 8.2**

  - [ ]* 10.4 Write property test for statistics accuracy
    - **Property 23: Processing statistics accuracy**
    - **Validates: Requirements 8.5**

  - [x] 10.5 Implement JSON export functionality
    - Export chunks to JSON format
    - Handle numpy array serialization
    - Support vector database format
    - _Requirements: 8.3, 8.4_

  - [ ]* 10.6 Write unit tests for orchestrator
    - Test end-to-end processing of simple document
    - Test directory processing
    - Test JSON export
    - Test error handling
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Checkpoint - Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement error handling
  - [x] 12.1 Add parsing error handling
    - Handle invalid markdown/HTML
    - Handle encoding issues
    - Handle malformed structure
    - _Requirements: 1.1, 5.1, 5.2_

  - [x] 12.2 Add chunking error handling
    - Handle oversized code blocks
    - Handle empty sections
    - Handle circular references
    - _Requirements: 1.2, 1.3, 1.4_

  - [x] 12.3 Add embedding error handling
    - Implement retry with exponential backoff
    - Implement rate limiting
    - Handle batch failures
    - Handle model unavailability
    - _Requirements: 3.5_

  - [x] 12.4 Add summary generation error handling
    - Handle LLM failures with fallback
    - Implement timeout handling
    - Handle empty content
    - _Requirements: 7.4_

  - [x] 12.5 Add storage error handling
    - Check disk space before processing
    - Check write permissions
    - Handle JSON serialization errors
    - _Requirements: 8.1, 8.3_

  - [ ]* 12.6 Write unit tests for error handling
    - Test parsing error recovery
    - Test embedding failure and retry
    - Test summary fallback
    - Test storage error handling
    - _Requirements: 3.5, 7.4_

- [ ] 13. Create command-line interface
  - [x] 13.1 Create chunk_user_manuals.py script
    - Accept input directory or file path
    - Accept output directory
    - Accept configuration parameters (chunk sizes, overlap, models)
    - Support dry-run mode
    - Display progress and statistics
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ]* 13.2 Write integration tests for CLI
    - Test single file processing
    - Test directory processing
    - Test configuration parameter handling
    - Test dry-run mode
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 14. Integrate with existing pipeline
  - [x] 14.1 Update crawl_pipeline.py
    - Add --process-manuals flag
    - Add manual processing step after local file crawling
    - Pass configuration from environment variables
    - _Requirements: 8.1_

  - [x] 14.2 Extend code_summarizer.py
    - Add generate_documentation_summary function
    - Use documentation-specific prompts
    - Integrate with UserManualChunker
    - _Requirements: 7.1, 7.2_

  - [x] 14.3 Update database schema
    - Add content_type field to distinguish documentation from code
    - Add heading_hierarchy indexing
    - Ensure compatibility with existing vector storage
    - _Requirements: 8.1, 8.4_

  - [ ]* 14.4 Write integration tests for pipeline
    - Test end-to-end pipeline with manual processing
    - Test database storage and retrieval
    - Test integration with existing RAG queries
    - _Requirements: 8.1, 8.4_

- [ ] 15. Add configuration management
  - [ ] 15.1 Create configuration file support
    - Support .env configuration
    - Support YAML configuration file
    - Provide sensible defaults
    - Document all configuration options
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 15.2 Add configuration validation
    - Validate chunk size parameters
    - Validate model names
    - Validate file paths
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 16. Create documentation and examples
  - [ ] 16.1 Write README for user_manual_chunker module
    - Document installation
    - Document usage examples
    - Document configuration options
    - Document API reference
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 16.2 Create example scripts
    - Example: Process single markdown file
    - Example: Process directory of manuals
    - Example: Custom chunking strategy
    - Example: Custom metadata extractor
    - _Requirements: 10.5_

  - [ ] 16.3 Create tutorial notebook
    - Tutorial: Basic usage
    - Tutorial: Advanced configuration
    - Tutorial: Extending with custom parsers
    - Tutorial: Integration with RAG system
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 17. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Performance optimization
  - [ ] 18.1 Implement batch processing optimization
    - Optimize embedding batch size
    - Implement parallel document processing
    - Add progress tracking
    - _Requirements: 3.4_

  - [ ] 18.2 Implement caching
    - Cache parsed document structures
    - Cache embeddings for unchanged chunks
    - Implement cache invalidation
    - _Requirements: 8.1_

  - [ ] 18.3 Implement streaming for large documents
    - Stream document content instead of loading entirely
    - Process chunks incrementally
    - Reduce memory footprint
    - _Requirements: 1.1_

  - [ ]* 18.4 Write performance tests
    - Test processing time for typical manual
    - Test memory usage
    - Test batch processing efficiency
    - _Requirements: 3.4_
