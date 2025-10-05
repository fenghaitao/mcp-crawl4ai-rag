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