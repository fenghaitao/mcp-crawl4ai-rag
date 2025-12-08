# Batch Completions API

This document describes the batch chat completions API for processing multiple LLM requests concurrently.

## Overview

The batch completions API allows you to process multiple chat completion requests in parallel, significantly improving throughput for bulk operations. It supports both OpenAI and GitHub Copilot backends with automatic fallback handling.

## Features

- **Concurrent Processing**: Process multiple completions simultaneously using threading
- **Automatic Error Handling**: Failed requests return error responses without blocking others
- **Provider Support**: Works with OpenAI, GitHub Copilot, and local models
- **Rate Limiting**: Respects API rate limits with configurable concurrency
- **Detailed Logging**: Comprehensive metrics on batch processing performance
- **Token Tracking**: Aggregated token usage statistics across all completions

## API Reference

### `create_chat_completions_batch()`

Process multiple chat completion requests concurrently.

**Location**: `server/utils.py`

**Signature**:
```python
def create_chat_completions_batch(
    messages_list: List[List[Dict[str, str]]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 200,
    max_workers: int = 10,
    **kwargs
) -> List[Dict[str, Any]]
```

**Parameters**:
- `messages_list`: List of message lists, each containing message dictionaries with 'role' and 'content'
- `model`: Model to use (defaults to `MODEL_CHOICE` env var or "gpt-4o-mini")
- `temperature`: Temperature for generation (0.0-2.0)
- `max_tokens`: Maximum tokens to generate per completion
- `max_workers`: Maximum number of concurrent requests (default: 10)
- `**kwargs`: Additional parameters passed to the completion API

**Returns**:
- List of completion responses in the same order as input
- Each response is a dictionary with:
  - `choices`: List of completion choices
  - `model`: Model used
  - `usage`: Token usage statistics
  - `error`: Error message (only present if request failed)

**Example**:
```python
from server.utils import create_chat_completions_batch

# Prepare multiple requests
messages_list = [
    [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ],
    [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is JavaScript?"}
    ],
    [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Rust?"}
    ]
]

# Process all requests concurrently
results = create_chat_completions_batch(
    messages_list=messages_list,
    model="gpt-4o-mini",
    temperature=0.3,
    max_tokens=100,
    max_workers=5
)

# Access results
for i, result in enumerate(results):
    if "error" in result:
        print(f"Request {i} failed: {result['error']}")
    else:
        content = result["choices"][0]["message"]["content"]
        print(f"Response {i}: {content}")
```

## Provider-Specific Functions

### GitHub Copilot

**Location**: `llms/copilot_client.py`

```python
from llms.copilot_client import create_chat_completions_batch_copilot

results = create_chat_completions_batch_copilot(
    messages_list=messages_list,
    model="gpt-4o",
    temperature=0.3,
    max_tokens=200
)
```

The Copilot implementation uses async/await internally for efficient concurrent processing.

## Configuration

### Environment Variables

- `MODEL_CHOICE`: Default model to use (e.g., "gpt-4o-mini", "gpt-4o")
- `USE_COPILOT_CHAT`: Set to "true" to use GitHub Copilot instead of OpenAI
- `OPENAI_API_KEY`: OpenAI API key (required for OpenAI)
- `GITHUB_TOKEN`: GitHub token (required for Copilot)

### Concurrency Control

The `max_workers` parameter controls how many requests are processed simultaneously:

- **Lower values (1-5)**: Better for rate-limited APIs or when you want to be conservative
- **Higher values (10-20)**: Better for high-throughput scenarios with generous rate limits
- **Default (10)**: Balanced for most use cases

## Use Cases

### 1. Bulk Question Answering

Process multiple user questions in parallel:

```python
questions = [
    "What is the capital of France?",
    "Who invented the telephone?",
    "What is the speed of light?"
]

messages_list = [
    [{"role": "user", "content": q}]
    for q in questions
]

results = create_chat_completions_batch(messages_list)
```

### 2. Code Generation

Generate multiple code snippets concurrently:

```python
tasks = [
    "Write a function to sort a list",
    "Write a function to find duplicates",
    "Write a function to merge dictionaries"
]

messages_list = [
    [
        {"role": "system", "content": "You are a Python expert."},
        {"role": "user", "content": task}
    ]
    for task in tasks
]

results = create_chat_completions_batch(
    messages_list,
    temperature=0.2,
    max_tokens=300
)
```

### 3. Document Summarization

Summarize multiple documents in parallel:

```python
documents = [doc1_text, doc2_text, doc3_text]

messages_list = [
    [
        {"role": "system", "content": "Summarize the following text."},
        {"role": "user", "content": doc}
    ]
    for doc in documents
]

results = create_chat_completions_batch(
    messages_list,
    max_tokens=150
)
```

### 4. Contextual Embeddings

Generate contextual information for chunks (existing use case):

```python
# This is already used in your codebase for contextual embeddings
def generate_contextual_embeddings_batch(chunks, full_document):
    messages_list = [
        [
            {"role": "system", "content": "Provide context for this chunk."},
            {"role": "user", "content": f"Document: {full_document}\n\nChunk: {chunk}"}
        ]
        for chunk in chunks
    ]
    
    return create_chat_completions_batch(
        messages_list,
        temperature=0.3,
        max_tokens=200
    )
```

## Performance Considerations

### Throughput

With `max_workers=10`, you can expect:
- **OpenAI**: ~10-20 completions/second (depending on rate limits)
- **Copilot**: ~5-15 completions/second (depending on rate limits)

### Rate Limits

Be aware of API rate limits:
- **OpenAI**: Typically 3,500 RPM (requests per minute) for tier 1
- **Copilot**: ~60 RPM by default (configurable via `COPILOT_REQUESTS_PER_MINUTE`)

Adjust `max_workers` based on your rate limits to avoid throttling.

### Error Handling

The API handles errors gracefully:
- Failed requests return an error response instead of raising exceptions
- Other requests continue processing
- All results are returned in the original order

## Comparison with Single Requests

### Before (Sequential):
```python
results = []
for messages in messages_list:
    result = create_chat_completion(messages)
    results.append(result)
# Time: ~10 seconds for 10 requests
```

### After (Concurrent):
```python
results = create_chat_completions_batch(messages_list)
# Time: ~1-2 seconds for 10 requests (5-10x faster)
```

## Logging

The batch API provides detailed logging:

```
🔗 Chat Completion Batch Request
   📊 Batch size: 10
   🧵 Max workers: 10
   📋 Model: gpt-4o-mini
   🌡️  Temperature: 0.3
   🎛️  Max tokens: 200
   🤖 Provider: OpenAI
🚀 Processing completions concurrently...
✅ Batch completions finished!
   ⏱️  Total time: 1.23s
   📊 Success rate: 10/10 completions
   📈 Processing speed: 8.1 completions/second
   🎯 Total tokens - Prompt: 450, Completion: 890, Total: 1340
```

## Demo Script

Run the demo to see the API in action:

```bash
# Set up environment
export OPENAI_API_KEY='your-key'
# or
export GITHUB_TOKEN='your-token'
export USE_COPILOT_CHAT=true

# Run demo
python examples/demo_batch_completions.py
```

## Related APIs

- **Batch Embeddings**: `create_embeddings_batch()` - Process multiple embeddings concurrently
- **Single Completion**: `create_chat_completion()` - Process a single completion request

## Future Enhancements

Potential improvements for future versions:

1. **Async Batch API**: Support for OpenAI's file-based Batch API (50% cost savings)
2. **Adaptive Concurrency**: Automatically adjust `max_workers` based on rate limits
3. **Retry Logic**: Automatic retry with exponential backoff for failed requests
4. **Streaming Support**: Stream responses for batch requests
5. **Cost Tracking**: Track and report API costs per batch
