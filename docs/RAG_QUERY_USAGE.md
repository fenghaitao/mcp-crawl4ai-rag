# RAG Query Usage Guide

## Overview

The RAG (Retrieval-Augmented Generation) query command provides semantic search capabilities over ingested documentation and code. It uses vector embeddings to find the most relevant content chunks based on your query.

## Basic Usage

```bash
# Simple query
.venv/bin/python -m core rag query "What is Simics?"

# Limit number of results
.venv/bin/python -m core rag query "DML programming" --limit 10

# Filter by content type
.venv/bin/python -m core rag query "device model" --content-type documentation

# Apply similarity threshold
.venv/bin/python -m core rag query "Python API" --threshold 0.5

# JSON output for programmatic use
.venv/bin/python -m core rag query "configuration" --json
```

## Command Options

- `QUERY_TEXT` (required): The search query text
- `--limit, -l`: Number of results to return (default: 5)
- `--threshold, -t`: Minimum similarity threshold (default: no threshold)
- `--content-type`: Filter by content type (`documentation`, `code_dml`, `python_test`)
- `--json`: Output results in JSON format

## Output Format

### Human-Readable Output

The default output shows:
- Similarity score (higher is better, though may be negative for unnormalized embeddings)
- Source file path
- Chunk number within the file
- Summary of the chunk
- Content preview (first 300 characters)
- Relevant metadata (title, section, word count, code presence)

### JSON Output

Use `--json` flag to get structured output suitable for programmatic processing:

```json
{
  "query": "your query text",
  "limit": 5,
  "threshold": null,
  "content_type": null,
  "result_count": 3,
  "results": [
    {
      "chunk_id": "...",
      "file_id": 123,
      "url": "path/to/file.md",
      "chunk_number": 0,
      "similarity": 0.85,
      "summary": "...",
      "content_preview": "...",
      "metadata": {...}
    }
  ]
}
```

## Backend Support

The semantic search works with both database backends:

### ChromaDB
- Uses ChromaDB's native vector search
- Embeddings are stored directly in the collection
- Fast local search without external dependencies

### Supabase
- Attempts to use Supabase's `match_content_chunks` RPC function
- Falls back to client-side similarity computation if RPC not available
- Supports cloud-based vector search

## Embedding Generation

The query embedding is generated using the same embedding model that was used during document ingestion:
- GitHub Copilot embeddings (default)
- OpenAI embeddings (fallback)
- Qwen embeddings (if configured)

This ensures consistency between query and document embeddings for accurate similarity matching.

## Examples

### Find documentation about a specific topic
```bash
.venv/bin/python -m core rag query "device configuration" --limit 5
```

### Search for code examples
```bash
.venv/bin/python -m core rag query "register access" --content-type code_dml
```

### Get high-confidence results only
```bash
.venv/bin/python -m core rag query "memory mapping" --threshold 0.7
```

### Export results for processing
```bash
.venv/bin/python -m core rag query "API reference" --json > results.json
```

## Integration with RAG Pipeline

The semantic search is integrated with the document ingestion pipeline:

1. **Ingest documents**: `python -m core rag ingest-doc <file>`
2. **Query documents**: `python -m core rag query "your query"`
3. **View results**: Results include file paths, summaries, and content

## Troubleshooting

### No results found
- Try lowering or removing the threshold: `--threshold 0.0` or omit `--threshold`
- Check if documents are ingested: `python -m core db stats`
- Verify database connection: `python -m core status`

### Embedding dimension mismatch
- Ensure the same embedding model is used for ingestion and querying
- Check environment variables: `USE_QWEN_EMBEDDINGS`, `USE_COPILOT_EMBEDDINGS`

### Low similarity scores
- Similarity scores range from 0 to 1 (higher is better)
- Scores above 0.5 indicate good relevance
- Scores between 0.2-0.5 indicate moderate relevance
- Scores below 0.2 may not be very relevant
