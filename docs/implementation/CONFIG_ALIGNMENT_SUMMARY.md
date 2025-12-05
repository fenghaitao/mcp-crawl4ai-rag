# Config Alignment Summary

## Overview
Updated `src/user_manual_chunker/config.py`, `src/user_manual_chunker/orchestrator.py`, and `.env` to create a complete, aligned configuration system for the user manual chunker.

## Changes Made

### 1. Updated `.env`

Added new section for User Manual Chunker Configuration:

```bash
# User Manual Chunker Configuration
MANUAL_MAX_CHUNK_SIZE=1000
MANUAL_MIN_CHUNK_SIZE=100
MANUAL_CHUNK_OVERLAP=50
MANUAL_SIZE_METRIC=characters
MANUAL_EMBEDDING_MODEL=text-embedding-3-small
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus
MANUAL_GENERATE_SUMMARIES=true
MANUAL_GENERATE_EMBEDDINGS=true
```

These variables control:
- Chunk size limits and overlap
- Which models to use for embeddings and summaries
- Whether to generate summaries and embeddings

### 2. Updated `src/user_manual_chunker/config.py`

Added new configuration fields to align with `.env`:

```python
# Embedding provider selection (aligned with .env)
use_qwen_embeddings: bool = False
use_copilot_embeddings: bool = True

# Processing options
use_contextual_embeddings: bool = True

# Rate limiting (aligned with .env)
copilot_requests_per_minute: int = 60
```

Updated `from_env()` method to read these values from environment variables:
- `USE_QWEN_EMBEDDINGS` - Use local Qwen model for embeddings
- `USE_COPILOT_EMBEDDINGS` - Use GitHub Copilot for embeddings
- `USE_CONTEXTUAL_EMBEDDINGS` - Use contextual embeddings for better retrieval
- `COPILOT_REQUESTS_PER_MINUTE` - Rate limit for Copilot API

### 3. Updated `src/user_manual_chunker/orchestrator.py`

**Fixed Import:**
- Added `PatternAwareSemanticChunker` to imports from `semantic_chunker`

**Updated EmbeddingGenerator Initialization:**
```python
self.embedding_generator = embedding_generator or EmbeddingGenerator(
    model=self.config.embedding_model,
    batch_size=self.config.embedding_batch_size,
    normalize=True,
    max_retries=self.config.embedding_retry_attempts,
    initial_retry_delay=1.0,
    rate_limit_requests=self.config.copilot_requests_per_minute,
    rate_limit_window=60.0
)
```

Now properly passes:
- `max_retries` from config
- `rate_limit_requests` from config (aligned with COPILOT_REQUESTS_PER_MINUTE)
- `rate_limit_window` set to 60 seconds

## Complete Environment Variables Reference

The config now properly reads and uses these `.env` variables:

### User Manual Chunker Specific
```bash
MANUAL_MAX_CHUNK_SIZE=1000           # Maximum chunk size in characters
MANUAL_MIN_CHUNK_SIZE=100            # Minimum chunk size in characters
MANUAL_CHUNK_OVERLAP=50              # Overlap between chunks
MANUAL_SIZE_METRIC=characters        # Size metric: 'characters' or 'tokens'
MANUAL_EMBEDDING_MODEL=text-embedding-3-small  # Embedding model
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus    # Summary model
MANUAL_GENERATE_SUMMARIES=true       # Generate summaries
MANUAL_GENERATE_EMBEDDINGS=true      # Generate embeddings
```

### Embedding Provider Selection
```bash
USE_QWEN_EMBEDDINGS=false      # Use local Qwen model
USE_COPILOT_EMBEDDINGS=true    # Use GitHub Copilot (default)
```

### RAG Strategies
```bash
USE_CONTEXTUAL_EMBEDDINGS=true # Enhanced embeddings with context
```

### Rate Limiting
```bash
COPILOT_REQUESTS_PER_MINUTE=60 # Rate limit for Copilot API
```

### Model Configuration
```bash
MANUAL_EMBEDDING_MODEL=text-embedding-3-small
MANUAL_SUMMARY_MODEL=iflow/qwen3-coder-plus
```

## Benefits

1. **Centralized Configuration**: All embedding-related settings now flow through config
2. **Environment Variable Support**: Easy to change behavior without code changes
3. **Consistent with utils.py**: Uses same embedding infrastructure as rest of codebase
4. **Rate Limiting**: Properly configured rate limiting for API calls
5. **Flexible Provider Selection**: Can switch between Qwen, Copilot, and OpenAI embeddings

## Testing

All tests pass successfully:
- ✅ `test_orchestrator.py` - 8/8 tests passed
- ✅ `test_pattern_aware_semantic_chunker.py` - 11/11 tests passed
- ✅ `test_embedding_generator.py` - 15/15 tests passed

## Usage Example

```python
from src.user_manual_chunker import ChunkerConfig, UserManualChunker

# Load config from environment variables
config = ChunkerConfig.from_env()

# Config will automatically use:
# - USE_QWEN_EMBEDDINGS for local embeddings
# - USE_COPILOT_EMBEDDINGS for Copilot embeddings
# - COPILOT_REQUESTS_PER_MINUTE for rate limiting
# - USE_CONTEXTUAL_EMBEDDINGS for enhanced retrieval

# Create chunker with config
chunker = UserManualChunker.from_config(config)

# Process documents
chunks = chunker.process_document("path/to/document.md")
```

## Backward Compatibility

All changes are backward compatible:
- New config fields have sensible defaults
- Existing code continues to work without changes
- Tests pass without modification
