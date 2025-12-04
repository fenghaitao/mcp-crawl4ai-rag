# Design Document

## Overview

This design specifies a chunking and embedding solution for technical user manual documents optimized for Retrieval-Augmented Generation (RAG). The system processes markdown and HTML documentation (such as the Simics DML 1.4 Reference Manual) by intelligently segmenting content while preserving semantic coherence, extracting hierarchical metadata, and generating embeddings suitable for semantic search.

The solution extends the existing astchunk infrastructure and integrates with the current RAG pipeline (crawl_pipeline.py, code_summarizer.py) to provide specialized handling for documentation that contains structured sections, code examples, and technical specifications.

## Architecture

The system follows a pipeline architecture with four main stages:

1. **Document Parsing**: Parse markdown/HTML documents to extract structure (headings, paragraphs, code blocks, lists)
2. **Intelligent Chunking**: Segment documents at semantic boundaries while respecting size constraints and preserving code block integrity
3. **Metadata Extraction**: Extract hierarchical section information, code language detection, and document provenance
4. **Embedding Generation**: Generate dense vector embeddings using technical documentation-optimized models

The architecture uses a plugin-based design to support multiple document formats and chunking strategies:

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Input                            │
│              (Markdown, HTML, Plain Text)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Document Parser                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Markdown   │  │     HTML     │  │  Plain Text  │      │
│  │    Parser    │  │    Parser    │  │    Parser    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Document Structure (AST)                        │
│    Headings, Paragraphs, Code Blocks, Lists, Tables         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Semantic Chunker                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Chunking Strategy:                              │       │
│  │  - Respect section boundaries                    │       │
│  │  - Keep code blocks intact                       │       │
│  │  - Maintain context with overlaps                │       │
│  │  - Split at paragraph boundaries                 │       │
│  └──────────────────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Metadata Extractor                              │
│  - Section hierarchy (H1 > H2 > H3)                         │
│  - Code language detection                                   │
│  - Document source path                                      │
│  - Content type classification                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Summary Generator                               │
│  - LLM-based chunk summarization                            │
│  - Context-aware descriptions                                │
│  - Fallback to extractive summaries                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Embedding Generator                             │
│  - Batch processing for efficiency                          │
│  - Technical documentation model                             │
│  - Vector normalization                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Output Storage                              │
│  JSON format with content, metadata, embeddings, summary     │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. DocumentParser (Abstract Base Class)

**Purpose**: Parse different document formats into a unified structure

**Interface**:
```python
class DocumentParser(ABC):
    @abstractmethod
    def parse(self, content: str) -> DocumentStructure:
        """Parse document content into structured representation"""
        pass
    
    @abstractmethod
    def extract_headings(self, content: str) -> List[Heading]:
        """Extract heading hierarchy"""
        pass
    
    @abstractmethod
    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """Extract code blocks with language info"""
        pass
```

**Implementations**:
- `MarkdownParser`: Parses markdown using regex and markdown libraries
- `HTMLParser`: Parses HTML using BeautifulSoup
- `PlainTextParser`: Basic text parsing with heuristic structure detection

### 2. DocumentStructure

**Purpose**: Unified representation of parsed document

**Data Model**:
```python
@dataclass
class Heading:
    level: int  # 1-6 for H1-H6
    text: str
    line_number: int
    parent: Optional['Heading'] = None

@dataclass
class CodeBlock:
    content: str
    language: str
    line_start: int
    line_end: int
    preceding_text: Optional[str] = None  # Explanatory text before code

@dataclass
class Paragraph:
    content: str
    line_start: int
    line_end: int

@dataclass
class DocumentStructure:
    source_path: str
    headings: List[Heading]
    paragraphs: List[Paragraph]
    code_blocks: List[CodeBlock]
    raw_content: str
    
    def get_section(self, heading: Heading) -> Section:
        """Get all content under a heading until next same-level heading"""
        pass
```

### 3. SemanticChunker

**Purpose**: Intelligently chunk documents while preserving semantic coherence

**Interface**:
```python
class SemanticChunker:
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        chunk_overlap: int = 50,
        size_metric: str = "characters"  # or "tokens"
    ):
        pass
    
    def chunk_document(
        self,
        doc_structure: DocumentStructure
    ) -> List[DocumentChunk]:
        """Chunk document respecting semantic boundaries"""
        pass
    
    def _should_split_section(self, section: Section) -> bool:
        """Determine if section exceeds size limits"""
        pass
    
    def _split_at_paragraph_boundary(
        self,
        section: Section
    ) -> List[DocumentChunk]:
        """Split large section at paragraph boundaries"""
        pass
    
    def _keep_code_with_context(
        self,
        code_block: CodeBlock,
        surrounding_text: str
    ) -> str:
        """Ensure code blocks stay with explanatory text"""
        pass
```

**Chunking Strategy**:
1. Start with section-level chunks (content under each heading)
2. If section exceeds max_chunk_size:
   - Split at paragraph boundaries
   - Keep code blocks with preceding explanatory paragraph
   - Include section heading in each split chunk
3. If section is below min_chunk_size:
   - Merge with adjacent sections at same level
4. Apply overlap by including last N characters/tokens of previous chunk

### 4. MetadataExtractor

**Purpose**: Extract structured metadata for each chunk

**Interface**:
```python
class MetadataExtractor:
    def extract(
        self,
        chunk: DocumentChunk,
        doc_structure: DocumentStructure
    ) -> ChunkMetadata:
        """Extract metadata for a chunk"""
        pass
    
    def _build_heading_hierarchy(
        self,
        chunk: DocumentChunk
    ) -> List[str]:
        """Build full heading path (H1 > H2 > H3)"""
        pass
    
    def _detect_code_language(
        self,
        code_block: CodeBlock
    ) -> str:
        """Detect programming language in code block"""
        pass
```

**Metadata Schema**:
```python
@dataclass
class ChunkMetadata:
    source_file: str
    heading_hierarchy: List[str]  # ["Introduction", "Language Features", "Data Types"]
    section_level: int  # Depth in document hierarchy
    contains_code: bool
    code_languages: List[str]  # ["dml", "python"]
    chunk_index: int  # Position in document
    line_start: int
    line_end: int
    char_count: int
    token_count: Optional[int] = None
```

### 5. SummaryGenerator

**Purpose**: Generate concise summaries for chunks

**Interface**:
```python
class SummaryGenerator:
    def __init__(
        self,
        model: str = "iflow/qwen3-coder-plus",
        max_summary_length: int = 150
    ):
        pass
    
    def generate_summary(
        self,
        chunk: DocumentChunk,
        doc_context: str,
        metadata: ChunkMetadata
    ) -> str:
        """Generate summary using LLM"""
        pass
    
    def _fallback_summary(
        self,
        chunk: DocumentChunk
    ) -> str:
        """Extractive summary fallback"""
        pass
```

### 6. EmbeddingGenerator

**Purpose**: Generate vector embeddings for chunks

**Interface**:
```python
class EmbeddingGenerator:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        batch_size: int = 32
    ):
        pass
    
    def generate_embeddings(
        self,
        chunks: List[DocumentChunk]
    ) -> List[np.ndarray]:
        """Generate embeddings in batches"""
        pass
    
    def _normalize_vectors(
        self,
        embeddings: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Normalize for cosine similarity"""
        pass
```

### 7. UserManualChunker (Main Orchestrator)

**Purpose**: Coordinate the entire chunking pipeline

**Interface**:
```python
class UserManualChunker:
    def __init__(
        self,
        parser: DocumentParser,
        chunker: SemanticChunker,
        metadata_extractor: MetadataExtractor,
        summary_generator: SummaryGenerator,
        embedding_generator: EmbeddingGenerator
    ):
        pass
    
    def process_document(
        self,
        file_path: str,
        generate_embeddings: bool = True,
        generate_summaries: bool = True
    ) -> List[ProcessedChunk]:
        """Process document end-to-end"""
        pass
    
    def process_directory(
        self,
        directory: str,
        pattern: str = "*.md"
    ) -> List[ProcessedChunk]:
        """Process multiple documents"""
        pass
    
    def export_to_json(
        self,
        chunks: List[ProcessedChunk],
        output_path: str
    ):
        """Export chunks to JSON format"""
        pass
```

## Data Models

### ProcessedChunk

Complete chunk with all generated data:

```python
@dataclass
class ProcessedChunk:
    chunk_id: str  # Unique identifier
    content: str  # Chunk text
    metadata: ChunkMetadata
    summary: Optional[str] = None
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": asdict(self.metadata),
            "summary": self.summary,
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        }
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Document structure parsing completeness
*For any* valid markdown document, parsing should extract all headings, paragraphs, and code blocks present in the document
**Validates: Requirements 1.1, 5.1**

### Property 2: Code block integrity preservation
*For any* document with code blocks, no code block should be split across multiple chunks
**Validates: Requirements 1.2, 1.4**

### Property 3: Section splitting at paragraph boundaries
*For any* section that exceeds maximum chunk size, all splits should occur at paragraph boundaries and no sentence should be broken
**Validates: Requirements 1.3, 6.3**

### Property 4: Heading context preservation in splits
*For any* section that is split into multiple chunks, each resulting chunk should contain the section heading
**Validates: Requirements 1.5, 6.1**

### Property 5: Heading hierarchy extraction
*For any* chunk from a document with headings, the metadata should contain the complete heading hierarchy path
**Validates: Requirements 2.1, 6.5**

### Property 6: Source file metadata presence
*For any* chunk, the metadata should contain the source file path
**Validates: Requirements 2.2**

### Property 7: Code language detection
*For any* code block, the system should identify and record the programming language
**Validates: Requirements 2.3**

### Property 8: Code presence flag accuracy
*For any* chunk, the contains_code metadata flag should accurately reflect whether code blocks are present
**Validates: Requirements 2.4**

### Property 9: Section level accuracy
*For any* chunk, the section_level metadata should match the actual depth in the document hierarchy
**Validates: Requirements 2.5**

### Property 10: Code syntax preservation in embeddings
*For any* chunk containing code, the code syntax should be preserved when passed to the embedding model
**Validates: Requirements 3.2**

### Property 11: Embedding vector normalization
*For any* generated embedding vector, the L2 norm should equal 1.0 (within floating point tolerance)
**Validates: Requirements 3.3**

### Property 12: Small section merging
*For any* section smaller than minimum size, it should be merged with adjacent sections while maintaining semantic boundaries
**Validates: Requirements 4.4**

### Property 13: Chunk overlap correctness
*For any* pair of adjacent chunks when overlap is enabled, the overlap region should match exactly and include complete sentences
**Validates: Requirements 4.5, 6.2**

### Property 14: HTML structure preservation
*For any* HTML document, parsing should extract text content while preserving the structural hierarchy
**Validates: Requirements 5.2**

### Property 15: Code block format recognition
*For any* document, the system should recognize both triple-backtick and indented code block formats
**Validates: Requirements 5.3**

### Property 16: Inline code marker preservation
*For any* chunk with inline code, the inline code markers should be preserved in the chunk text
**Validates: Requirements 5.4**

### Property 17: List item context preservation
*For any* list in a document, list items should remain together with their parent context
**Validates: Requirements 5.5**

### Property 18: Summary generation completeness
*For any* chunk, a summary should be generated (either via LLM or fallback)
**Validates: Requirements 7.1**

### Property 19: Code mention in summaries
*For any* chunk containing code blocks, the summary should mention code or programming concepts
**Validates: Requirements 7.2**

### Property 20: Summary length constraint
*For any* generated summary, the length should not exceed the configured maximum
**Validates: Requirements 7.5**

### Property 21: Output format completeness
*For any* processed chunk, the output should contain content, metadata, and embeddings (if enabled)
**Validates: Requirements 8.1**

### Property 22: Chunk ID uniqueness
*For any* set of chunks from a document, all chunk IDs should be unique
**Validates: Requirements 8.2**

### Property 23: Processing statistics accuracy
*For any* document processing operation, the reported statistics should accurately reflect the actual chunk count and sizes
**Validates: Requirements 8.5**

### Property 24: API documentation pattern preservation
*For any* API documentation section, function signatures should remain with their descriptions
**Validates: Requirements 9.1**

### Property 25: Grammar rule and example cohesion
*For any* grammar specification section, grammar rules should remain together with their examples
**Validates: Requirements 9.2**

### Property 26: Definition list cohesion
*For any* definition list, terms should remain with their definitions
**Validates: Requirements 9.3**

### Property 27: Table structure preservation
*For any* table in a document, the table structure should be preserved in the chunk text
**Validates: Requirements 9.4**

### Property 28: Cross-reference link preservation
*For any* cross-reference in a document, the reference link should be preserved in the chunk content
**Validates: Requirements 9.5**

## Error Handling

The system implements graceful error handling at each stage:

### Parsing Errors
- **Invalid Markdown/HTML**: Log warning and attempt best-effort parsing
- **Encoding Issues**: Try multiple encodings (UTF-8, Latin-1, CP1252)
- **Malformed Structure**: Use heuristics to recover structure

### Chunking Errors
- **Oversized Code Blocks**: If a single code block exceeds max_chunk_size, create a chunk containing only that code block with a warning
- **Empty Sections**: Skip empty sections and log info message
- **Circular References**: Detect and break circular heading hierarchies

### Embedding Errors
- **API Failures**: Retry with exponential backoff (3 attempts)
- **Rate Limiting**: Implement token bucket rate limiter
- **Batch Failures**: Process failed chunks individually
- **Model Unavailable**: Fall back to alternative embedding model if configured

### Summary Generation Errors
- **LLM Failures**: Use fallback extractive summary (first sentence or heading)
- **Timeout**: Set 30-second timeout, use fallback on timeout
- **Empty Content**: Generate summary from metadata

### Storage Errors
- **Disk Full**: Fail fast with clear error message
- **Permission Denied**: Check write permissions before processing
- **JSON Serialization**: Handle non-serializable types (convert numpy arrays to lists)

## Testing Strategy

The testing strategy employs both unit tests and property-based tests to ensure correctness:

### Unit Tests

Unit tests verify specific examples and edge cases:

1. **Parser Tests**:
   - Parse simple markdown with headings and paragraphs
   - Parse markdown with code blocks in various formats
   - Parse HTML with nested structure
   - Handle malformed input gracefully

2. **Chunker Tests**:
   - Chunk small document (single chunk)
   - Chunk large document (multiple chunks)
   - Handle document with only code blocks
   - Handle document with no structure

3. **Metadata Tests**:
   - Extract flat heading hierarchy (H1 only)
   - Extract nested heading hierarchy (H1 > H2 > H3)
   - Detect code languages (Python, DML, JavaScript)
   - Handle missing metadata gracefully

4. **Integration Tests**:
   - Process complete Simics DML manual page
   - Process API reference documentation
   - Process grammar specification
   - End-to-end pipeline with real documents

### Property-Based Tests

Property-based tests verify universal properties across many generated inputs. We will use the `hypothesis` library for Python to generate test cases.

**Test Configuration**:
- Each property test should run a minimum of 100 iterations
- Use appropriate generators for document structures
- Shrink failing examples to minimal reproducible cases

**Property Test Implementations**:

Each correctness property listed above will be implemented as a property-based test. The tests will:

1. Generate random document structures with varying:
   - Heading hierarchies (1-6 levels deep)
   - Section sizes (small, medium, large)
   - Code block placements and languages
   - Paragraph counts and lengths

2. Apply the chunking pipeline

3. Verify the property holds for all generated chunks

**Test Tagging**:
Each property-based test must include a comment tag referencing the design document:
```python
# Feature: user-manual-rag, Property 2: Code block integrity preservation
@given(documents_with_code_blocks())
def test_code_block_integrity(document):
    chunks = chunker.chunk_document(document)
    # Verify no code block is split...
```

### Test Data Generators

Custom generators for property-based testing:

```python
@composite
def markdown_documents(draw):
    """Generate random markdown documents"""
    num_sections = draw(integers(min_value=1, max_value=10))
    sections = []
    for _ in range(num_sections):
        heading_level = draw(integers(min_value=1, max_value=3))
        heading_text = draw(text(min_size=5, max_size=50))
        num_paragraphs = draw(integers(min_value=1, max_value=5))
        has_code = draw(booleans())
        # Build section...
    return Document(sections)

@composite
def documents_with_code_blocks(draw):
    """Generate documents guaranteed to have code blocks"""
    # Ensure at least one code block per section...
    pass

@composite
def large_sections(draw):
    """Generate sections that exceed max_chunk_size"""
    # Generate large content...
    pass
```

## Integration with Existing System

The user manual chunker integrates with the existing RAG pipeline:

### Integration Points

1. **crawl_pipeline.py**: Add new step for user manual processing
   ```python
   # After local file crawling
   if args.process_manuals:
       manual_success = run_command([
           python_exe, "scripts/chunk_user_manuals.py",
           str(downloaded_pages_dir),
           "--output-dir", str(output_dir / "manual_chunks")
       ], "User Manual Chunking")
   ```

2. **code_summarizer.py**: Extend for documentation summaries
   - Add `generate_documentation_summary()` function
   - Use documentation-specific prompts
   - Integrate with existing iflow_client

3. **Database Storage**: Store chunks in existing vector database
   - Use same schema as code chunks
   - Add `content_type` field to distinguish documentation from code
   - Index on `heading_hierarchy` for hierarchical retrieval

### Configuration

Add configuration to `.env`:
```bash
# User Manual Chunking Configuration
MANUAL_MAX_CHUNK_SIZE=1000
MANUAL_MIN_CHUNK_SIZE=100
MANUAL_CHUNK_OVERLAP=50
MANUAL_SIZE_METRIC=characters  # or tokens
MANUAL_EMBEDDING_MODEL=text-embedding-3-small
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus
MANUAL_GENERATE_SUMMARIES=true
MANUAL_GENERATE_EMBEDDINGS=true
```

### Output Format

Chunks are exported to JSON with the following schema:
```json
{
  "chunks": [
    {
      "chunk_id": "simics_dml_language_md_0001",
      "content": "# Device Modeling Language\n\nDML is a domain-specific language...",
      "metadata": {
        "source_file": "pipeline_output/downloaded_pages/simics_docs_dml-1.4-reference-manual_language.md",
        "heading_hierarchy": ["Device Modeling Language", "Overview"],
        "section_level": 2,
        "contains_code": true,
        "code_languages": ["dml"],
        "chunk_index": 1,
        "line_start": 1,
        "line_end": 45,
        "char_count": 987,
        "token_count": 234
      },
      "summary": "Introduction to DML as a domain-specific language for device modeling with code examples",
      "embedding": [0.123, -0.456, 0.789, ...]
    }
  ],
  "statistics": {
    "total_chunks": 156,
    "average_chunk_size": 892,
    "total_code_blocks": 78,
    "processing_time_seconds": 45.2
  }
}
```

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: Process embeddings in batches of 32 chunks
2. **Parallel Processing**: Use multiprocessing for independent documents
3. **Caching**: Cache parsed document structures for reprocessing
4. **Lazy Loading**: Load document content on-demand
5. **Streaming**: Stream large documents instead of loading entirely into memory

### Expected Performance

For a typical user manual (e.g., Simics DML Reference Manual):
- **Document Size**: ~500KB markdown
- **Chunk Count**: ~150-200 chunks
- **Processing Time**: ~30-60 seconds (including embeddings)
- **Memory Usage**: ~200MB peak

### Scalability

The system should handle:
- Single documents up to 10MB
- Batch processing of 100+ documents
- Concurrent processing of 4-8 documents (based on CPU cores)

## Dependencies

### Required Libraries

```python
# Core dependencies
markdown>=3.4.0  # Markdown parsing
beautifulsoup4>=4.12.0  # HTML parsing
lxml>=4.9.0  # XML/HTML parsing backend

# NLP and embeddings
numpy>=1.24.0  # Vector operations
tiktoken>=0.5.0  # Token counting for OpenAI models

# Testing
pytest>=7.4.0  # Unit testing
hypothesis>=6.82.0  # Property-based testing

# Existing project dependencies
# (already in requirements)
# - iflow_client for embeddings and summaries
# - supabase for vector storage
```

### External Services

- **iFlow API**: For embeddings and summary generation
- **Supabase**: For vector storage and retrieval

## Future Enhancements

1. **Multi-language Support**: Extend parsers for other documentation formats (reStructuredText, AsciiDoc)
2. **Semantic Chunking**: Use sentence embeddings to find optimal split points
3. **Cross-reference Resolution**: Resolve and embed linked content
4. **Incremental Updates**: Only reprocess changed documents
5. **Query-time Chunking**: Dynamically adjust chunk boundaries based on query context
6. **Hierarchical Retrieval**: Retrieve parent/child chunks for better context
