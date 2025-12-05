# User Manual Chunker - Quick Start Guide

## Overview
The User Manual Chunker is a complete pipeline for processing technical documentation into RAG-ready chunks with embeddings, summaries, and metadata.

## Features
- ✅ Flexible embedding providers (Qwen, Copilot, OpenAI)
- ✅ Automatic provider fallback
- ✅ Pattern-aware semantic chunking
- ✅ Metadata extraction
- ✅ Summary generation
- ✅ Rate limiting and retry logic
- ✅ Full environment variable configuration

## Quick Start

### 1. Configure Environment Variables

Edit `.env` to set your preferences:

```bash
# Embedding Provider (choose one or use fallback chain)
USE_QWEN_EMBEDDINGS=false      # Local model (no API costs)
USE_COPILOT_EMBEDDINGS=true    # GitHub Copilot (default)
# Falls back to OpenAI if both are false

# Chunking Settings
MANUAL_MAX_CHUNK_SIZE=1000
MANUAL_MIN_CHUNK_SIZE=100
MANUAL_CHUNK_OVERLAP=50

# Processing Options
MANUAL_GENERATE_SUMMARIES=true
MANUAL_GENERATE_EMBEDDINGS=true
USE_CONTEXTUAL_EMBEDDINGS=true

# Rate Limiting
COPILOT_REQUESTS_PER_MINUTE=60
```

### 2. Basic Usage

```python
from src.user_manual_chunker import ChunkerConfig, UserManualChunker

# Load config from environment
config = ChunkerConfig.from_env()

# Create chunker
chunker = UserManualChunker.from_config(config)

# Process a single document
chunks = chunker.process_document("path/to/document.md")

# Export to JSON
chunker.export_to_json(chunks, "output.json")

# Or export for vector database
chunker.export_to_vector_db_format(chunks, "vector_db.json")
```

### 3. Process Multiple Documents

```python
# Process entire directory
chunks = chunker.process_directory(
    directory="docs/",
    pattern="*.md",
    recursive=True
)

# Get statistics
stats = chunker.get_statistics()
print(f"Processed {stats['total_documents']} documents")
print(f"Created {stats['total_chunks']} chunks")
```

### 4. Custom Configuration

```python
# Create custom config
config = ChunkerConfig(
    max_chunk_size=1500,
    min_chunk_size=200,
    chunk_overlap=100,
    generate_summaries=True,
    generate_embeddings=True,
    use_contextual_embeddings=True
)

# Validate config
config.validate()

# Create chunker with custom config
chunker = UserManualChunker.from_config(config)
```

## Configuration Reference

### Chunking Parameters
- `MANUAL_MAX_CHUNK_SIZE` - Maximum chunk size (default: 1000)
- `MANUAL_MIN_CHUNK_SIZE` - Minimum chunk size (default: 100)
- `MANUAL_CHUNK_OVERLAP` - Overlap between chunks (default: 50)
- `MANUAL_SIZE_METRIC` - Size metric: 'characters' or 'tokens' (default: characters)

### Model Configuration
- `MANUAL_EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
- `MANUAL_SUMMARY_MODEL` - Summary model (default: iflow/qwen3-coder-plus)

### Embedding Provider Selection
- `USE_QWEN_EMBEDDINGS` - Use local Qwen model (default: false)
- `USE_COPILOT_EMBEDDINGS` - Use GitHub Copilot (default: true)
- Falls back to OpenAI if both are false

### Processing Options
- `MANUAL_GENERATE_SUMMARIES` - Generate summaries (default: true)
- `MANUAL_GENERATE_EMBEDDINGS` - Generate embeddings (default: true)
- `USE_CONTEXTUAL_EMBEDDINGS` - Enhanced embeddings (default: true)

### Rate Limiting
- `COPILOT_REQUESTS_PER_MINUTE` - Rate limit for Copilot API (default: 60)

## Output Format

### Standard JSON Export
```json
{
  "chunks": [
    {
      "chunk_id": "abc123_0001",
      "content": "Chunk text content...",
      "metadata": {
        "source_file": "document.md",
        "heading_hierarchy": ["Chapter 1", "Section 1.1"],
        "section_level": 2,
        "contains_code": true,
        "code_languages": ["python"],
        "chunk_index": 0,
        "line_start": 1,
        "line_end": 50,
        "char_count": 1000
      },
      "summary": "Summary of the chunk...",
      "embedding": [0.1, 0.2, ...]
    }
  ],
  "statistics": {
    "total_documents": 1,
    "total_chunks": 10,
    "total_code_blocks": 3,
    "average_chunk_size": 950.5,
    "processing_time_seconds": 12.34
  }
}
```

### Vector Database Format
```json
[
  {
    "id": "abc123_0001",
    "content": "Chunk text content...",
    "metadata": { ... },
    "summary": "Summary...",
    "embedding": [0.1, 0.2, ...]
  }
]
```

## Advanced Features

### Pattern-Aware Chunking
The chunker automatically detects and respects documentation patterns:
- Code blocks (preserves complete examples)
- Tables (keeps rows together)
- Lists (maintains list structure)
- Admonitions (keeps warnings/notes intact)

### Metadata Extraction
Each chunk includes rich metadata:
- Source file path
- Heading hierarchy (breadcrumb trail)
- Section level (depth in document)
- Code detection (boolean flag)
- Code languages (list of detected languages)
- Line numbers (start and end)
- Character count

### Summary Generation
Summaries are generated using the configured model:
- Context-aware (uses document structure)
- Concise (respects max_summary_length)
- Timeout protection (prevents hanging)

### Embedding Generation
Embeddings use the flexible provider system:
- Automatic fallback (Qwen → Copilot → OpenAI)
- Batch processing (efficient API usage)
- Rate limiting (respects API limits)
- Retry logic (handles transient failures)
- Vector normalization (for cosine similarity)

## Error Handling

The chunker includes robust error handling:
- Validates configuration before processing
- Handles file encoding issues
- Continues processing on individual chunk failures
- Tracks failed documents in statistics
- Provides detailed error logging

## Testing

Run tests to verify everything works:

```bash
# Test orchestrator
pytest test_orchestrator.py -v

# Test embedding generator
pytest test_embedding_generator.py -v

# Test pattern-aware chunker
pytest test_pattern_aware_semantic_chunker.py -v

# Run all tests
pytest test_orchestrator.py test_embedding_generator.py test_pattern_aware_semantic_chunker.py -v
```

## Troubleshooting

### Issue: Embeddings not generating
**Solution:** Check that `MANUAL_GENERATE_EMBEDDINGS=true` and you have valid API credentials for your chosen provider.

### Issue: Rate limit errors
**Solution:** Reduce `COPILOT_REQUESTS_PER_MINUTE` or increase delays between batches.

### Issue: Chunks too large/small
**Solution:** Adjust `MANUAL_MAX_CHUNK_SIZE` and `MANUAL_MIN_CHUNK_SIZE` in `.env`.

### Issue: Missing summaries
**Solution:** Ensure `MANUAL_GENERATE_SUMMARIES=true` and `MANUAL_SUMMARY_MODEL` is configured correctly.

## Performance Tips

1. **Batch Processing**: Process multiple documents at once using `process_directory()`
2. **Disable Summaries**: Set `MANUAL_GENERATE_SUMMARIES=false` for faster processing
3. **Use Local Embeddings**: Set `USE_QWEN_EMBEDDINGS=true` to avoid API rate limits
4. **Adjust Chunk Size**: Larger chunks = fewer API calls but less granular retrieval
5. **Tune Rate Limits**: Match `COPILOT_REQUESTS_PER_MINUTE` to your API tier

## Next Steps

- Integrate with vector database (Supabase, Pinecone, etc.)
- Build RAG application using the chunks
- Implement semantic search over documentation
- Add custom metadata extractors for domain-specific content
- Extend pattern handlers for specialized documentation formats
