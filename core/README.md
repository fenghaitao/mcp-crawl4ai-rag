# Scripts Directory

This directory contains utility scripts for the crawl4ai-mcp project.

## Available Scripts

### `download_hf_model.py`

Downloads embedding and reranking models used by the MCP server. Supports multiple models including lightweight and high-performance options.

**Available Models:**
- `ms-marco`: cross-encoder/ms-marco-MiniLM-L-6-v2 (22M params, ~90MB) - Default reranker
- `qwen-embedding`: Qwen/Qwen3-Embedding-0.6B (0.6B params, ~1.2GB) - High-quality embeddings  
- `qwen-reranker`: Qwen/Qwen3-Reranker-0.6B (0.6B params, ~1.2GB) - High-performance reranker

**Usage:**
```bash
# List available models
python scripts/download_hf_model.py --list

# Download default model (ms-marco)
python scripts/download_hf_model.py --models ms-marco

# Download Qwen models
python scripts/download_hf_model.py --models qwen-embedding --models qwen-reranker

# Download all models with testing
python scripts/download_hf_model.py --models all --test

# Use HF mirror endpoint (useful in regions with limited access)
python scripts/download_hf_model.py --models qwen-embedding --hf-endpoint https://hf-mirror.com --test
```

**Features:**
- Multiple model support (embedding + reranking models)
- Model-specific testing (reranking vs embedding tests)
- Support for custom Hugging Face endpoints
- CPU-optimized models with different performance/size tradeoffs
- Detailed progress and error reporting

**Requirements:**
- `sentence-transformers` package
- Internet connection for initial download (not needed if model is already cached)
- ~500MB-1GB RAM for model loading

The downloaded model will be cached in `~/.cache/huggingface/hub/` and automatically used by the MCP server when `USE_RERANKING=true` is set in the environment.

**Note:** Once downloaded, the model works offline. The script will use the cached version if available.

### `query_rag.py`

A command-line tool for testing and querying your RAG system. This script allows you to interactively search through crawled documents and code examples to verify your RAG database is working correctly.

**Usage:**
```bash
# Basic document search
python scripts/query_rag.py "How to create a DML device"

# Search only DML source files
python scripts/query_rag.py "register implementation" --source-type dml --count 5

# Search only Python source files  
python scripts/query_rag.py "device implementation" --source-type python

# Search both documents and code examples
python scripts/query_rag.py "interrupt handling" --type both --count 3

# Search only in web documentation (not source code)
python scripts/query_rag.py "DML syntax" --source-type docs

# Search both DML and Python source files
python scripts/query_rag.py "device configuration" --source-type source

# Use hybrid search (combines vector + keyword search)
python scripts/query_rag.py "memory mapping" --hybrid

# List available sources in your database
python scripts/query_rag.py --list-sources

# Verbose output with configuration details
python scripts/query_rag.py "device templates" --verbose
```

**Parameters:**
- `query`: The search query (required unless using --list-sources)
- `--source-type`: Filter by source type:
  - `docs`: Web documentation (e.g., intel.github.io)
  - `dml`: DML source files only
  - `python`: Python source files only  
  - `source`: Both DML and Python source files
  - `all`: All sources (default)
- `--type`: Search type:
  - `docs`: Search documents only (default)
  - `code`: Search code examples only
  - `both`: Search both documents and code examples
- `--count`: Number of results to return (default: 5)
- `--hybrid`: Enable hybrid search (vector + keyword)
- `--list-sources`: Show all available sources in database
- `--verbose`: Show detailed configuration and metadata

**Example Output:**
```
🔍 DOCUMENT SEARCH
==================================================
📄 Found 3 document(s):

🔸 Result #1
   📍 URL: file:///path/to/simics/device.dml
   📊 Similarity: 0.6891
   📦 Chunk #5
   📝 Content: This chunk provides a template for creating...
   🏷️  Metadata: {
      "device_name": "sja1000_can",
      "methods": ["filter", "write_access", ...],
      "source_id": "simics-dml"
   }
```

**Features:**
- **Smart Source Filtering**: Automatically filters by source type (docs, DML, Python)
- **Rich Metadata Display**: Shows file paths, device names, methods, classes, etc.
- **Similarity Scores**: Displays relevance scores for each result
- **Flexible Search Types**: Search documents only, code examples only, or both
- **Source Discovery**: List all available sources in your database
- **Hybrid Search Support**: Combines semantic and keyword search
- **Verbose Mode**: Shows configuration details and full metadata

**Requirements:**
- Configured `.env` file with database credentials
- At least one crawled source in your RAG database
- Same dependencies as the main MCP server
