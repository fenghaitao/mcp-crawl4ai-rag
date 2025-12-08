# Migration Guide: Optimizing with Batch Completions

This guide shows you how to update your existing code to use the new batch completions API for better performance.

## Overview

The batch completions API can significantly speed up any code that makes multiple sequential LLM calls. This guide identifies opportunities in your codebase and shows how to migrate.

## Identified Opportunities

### 1. Contextual Embeddings in `server/utils.py`

**Current Implementation (Sequential):**

```python
def add_documents_to_supabase(...):
    # ... existing code ...
    
    if use_contextual_embeddings:
        # Process in parallel using ThreadPoolExecutor
        process_args = []
        for j, content in enumerate(batch_contents):
            url = batch_urls[j]
            full_document = url_to_full_document.get(url, "")
            process_args.append((url, content, full_document))

        contextual_contents = [None] * len(batch_contents)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_idx = {executor.submit(process_chunk_with_context, arg): idx
                            for idx, arg in enumerate(process_args)}

            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result, success = future.result()
                    contextual_contents[idx] = result
                    if success:
                        batch_metadatas[idx]["contextual_embedding"] = True
                except Exception as e:
                    print(f"Error processing chunk {idx}: {e}")
                    contextual_contents[idx] = batch_contents[idx]
```

**Optimized Implementation (Batch):**

```python
def add_documents_to_supabase(...):
    # ... existing code ...
    
    if use_contextual_embeddings:
        # Prepare all messages at once
        messages_list = []
        for j, content in enumerate(batch_contents):
            url = batch_urls[j]
            full_document = url_to_full_document.get(url, "")
            
            prompt = f"""<document>
{full_document[:25000]}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{content}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
            
            messages_list.append([
                {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
                {"role": "user", "content": prompt}
            ])
        
        # Process all at once with batch API
        model_choice = os.getenv("MODEL_CHOICE")
        results = create_chat_completions_batch(
            messages_list=messages_list,
            model=model_choice,
            temperature=0.3,
            max_tokens=200,
            max_workers=10
        )
        
        # Process results
        contextual_contents = []
        for j, (content, result) in enumerate(zip(batch_contents, results)):
            if "error" not in result:
                context = result["choices"][0]["message"]["content"].strip()
                contextual_text = f"{context}\n---\n{content}"
                contextual_contents.append(contextual_text)
                batch_metadatas[j]["contextual_embedding"] = True
            else:
                print(f"Error processing chunk {j}: {result['error']}")
                contextual_contents.append(content)
```

**Benefits:**
- Simpler code (no manual ThreadPoolExecutor management)
- Better error handling
- Detailed logging
- Token usage tracking

### 2. Code Example Summaries in `server/utils.py`

**Current Implementation (Sequential):**

```python
def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
    """Generate a summary for a code example using its surrounding context."""
    model_choice = os.getenv("MODEL_CHOICE")

    prompt = f"""<context_before>
{context_before[-500:] if len(context_before) > 500 else context_before}
</context_before>

<code_example>
{code[:1500] if len(code) > 1500 else code}
</code_example>

<context_after>
{context_after[:500] if len(context_after) > 500 else context_after}
</context_after>

Based on the code example and its surrounding context, provide a concise summary (2-3 sentences) that describes what this code example demonstrates and its purpose. Focus on the practical application and key concepts illustrated.
"""

    try:
        response = create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise code example summaries."},
                {"role": "user", "content": prompt}
            ],
            model=model_choice,
            temperature=0.3,
            max_tokens=100
        )

        return response["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"Error generating code example summary: {e}")
        return "Code example for demonstration purposes."
```

**Optimized Implementation (Batch):**

```python
def generate_code_example_summaries_batch(
    code_examples: List[str],
    contexts_before: List[str],
    contexts_after: List[str]
) -> List[str]:
    """
    Generate summaries for multiple code examples concurrently.
    
    Args:
        code_examples: List of code example strings
        contexts_before: List of context before each code example
        contexts_after: List of context after each code example
        
    Returns:
        List of summary strings
    """
    model_choice = os.getenv("MODEL_CHOICE")
    
    # Prepare all messages
    messages_list = []
    for code, ctx_before, ctx_after in zip(code_examples, contexts_before, contexts_after):
        prompt = f"""<context_before>
{ctx_before[-500:] if len(ctx_before) > 500 else ctx_before}
</context_before>

<code_example>
{code[:1500] if len(code) > 1500 else code}
</code_example>

<context_after>
{ctx_after[:500] if len(ctx_after) > 500 else ctx_after}
</context_after>

Based on the code example and its surrounding context, provide a concise summary (2-3 sentences) that describes what this code example demonstrates and its purpose. Focus on the practical application and key concepts illustrated.
"""
        
        messages_list.append([
            {"role": "system", "content": "You are a helpful assistant that provides concise code example summaries."},
            {"role": "user", "content": prompt}
        ])
    
    # Process all at once
    results = create_chat_completions_batch(
        messages_list=messages_list,
        model=model_choice,
        temperature=0.3,
        max_tokens=100,
        max_workers=10
    )
    
    # Extract summaries
    summaries = []
    for result in results:
        if "error" not in result:
            summary = result["choices"][0]["message"]["content"].strip()
            summaries.append(summary)
        else:
            print(f"Error generating summary: {result['error']}")
            summaries.append("Code example for demonstration purposes.")
    
    return summaries


# Keep the single version for backward compatibility
def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
    """Generate a summary for a single code example."""
    summaries = generate_code_example_summaries_batch([code], [context_before], [context_after])
    return summaries[0]
```

**Usage in `add_code_examples_to_supabase`:**

```python
def add_code_examples_to_supabase(...):
    # ... existing code ...
    
    # OLD: Sequential processing
    # for code, ctx_before, ctx_after in zip(code_examples, contexts_before, contexts_after):
    #     summary = generate_code_example_summary(code, ctx_before, ctx_after)
    #     summaries.append(summary)
    
    # NEW: Batch processing
    summaries = generate_code_example_summaries_batch(
        code_examples=code_examples,
        contexts_before=contexts_before,
        contexts_after=contexts_after
    )
```

### 3. Source Summaries in `server/utils.py`

**Current Implementation (Sequential):**

```python
def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
    """Extract a summary for a source from its content using an LLM."""
    # ... existing code ...
    
    try:
        response = create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise library/tool/framework summaries."},
                {"role": "user", "content": prompt}
            ],
            model=model_choice,
            temperature=0.3,
            max_tokens=150
        )

        summary = response["choices"][0]["message"]["content"].strip()
        # ... rest of code ...
```

**Optimized Implementation (Batch):**

```python
def extract_source_summaries_batch(
    source_ids: List[str],
    contents: List[str],
    max_length: int = 500
) -> List[str]:
    """
    Extract summaries for multiple sources concurrently.
    
    Args:
        source_ids: List of source IDs
        contents: List of content strings
        max_length: Maximum length of each summary
        
    Returns:
        List of summary strings
    """
    model_choice = os.getenv("MODEL_CHOICE")
    
    # Prepare all messages
    messages_list = []
    for source_id, content in zip(source_ids, contents):
        if not content or len(content.strip()) == 0:
            messages_list.append(None)  # Skip empty content
            continue
        
        truncated_content = content[:25000] if len(content) > 25000 else content
        
        prompt = f"""<source_content>
{truncated_content}
</source_content>

The above content is from the documentation for '{source_id}'. Please provide a concise summary (3-5 sentences) that describes what this library/tool/framework is about. The summary should help understand what the library/tool/framework accomplishes and the purpose.
"""
        
        messages_list.append([
            {"role": "system", "content": "You are a helpful assistant that provides concise library/tool/framework summaries."},
            {"role": "user", "content": prompt}
        ])
    
    # Filter out None values and track indices
    valid_messages = [(i, msg) for i, msg in enumerate(messages_list) if msg is not None]
    valid_indices = [i for i, _ in valid_messages]
    valid_messages_list = [msg for _, msg in valid_messages]
    
    # Process all at once
    if valid_messages_list:
        results = create_chat_completions_batch(
            messages_list=valid_messages_list,
            model=model_choice,
            temperature=0.3,
            max_tokens=150,
            max_workers=10
        )
    else:
        results = []
    
    # Build final summaries list
    summaries = []
    result_idx = 0
    for i, source_id in enumerate(source_ids):
        if i in valid_indices:
            result = results[result_idx]
            result_idx += 1
            
            if "error" not in result:
                summary = result["choices"][0]["message"]["content"].strip()
                if len(summary) > max_length:
                    summary = summary[:max_length] + "..."
                summaries.append(summary)
            else:
                print(f"Error generating summary for {source_id}: {result['error']}")
                summaries.append(f"Content from {source_id}")
        else:
            summaries.append(f"Content from {source_id}")
    
    return summaries


# Keep single version for backward compatibility
def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
    """Extract a summary for a single source."""
    summaries = extract_source_summaries_batch([source_id], [content], max_length)
    return summaries[0]
```

## Migration Checklist

### Step 1: Update Imports

Add the batch completion import to files that need it:

```python
from server.utils import (
    create_chat_completion,
    create_chat_completions_batch,  # Add this
    create_embeddings_batch,
    # ... other imports
)
```

### Step 2: Identify Sequential Patterns

Look for these patterns in your code:

```python
# Pattern 1: Loop with LLM calls
results = []
for item in items:
    result = create_chat_completion(...)
    results.append(result)

# Pattern 2: ThreadPoolExecutor with single completions
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(create_chat_completion, ...) for item in items]
    results = [f.result() for f in futures]
```

### Step 3: Convert to Batch

Replace with batch processing:

```python
# Prepare all messages
messages_list = [prepare_messages(item) for item in items]

# Process in batch
results = create_chat_completions_batch(
    messages_list=messages_list,
    model="gpt-4o-mini",
    max_workers=10
)
```

### Step 4: Test

1. Run unit tests: `pytest tests/unit/test_batch_completions.py`
2. Test with small batches first
3. Monitor performance and adjust `max_workers`
4. Check error handling

### Step 5: Monitor

Track improvements:

```python
import time

# Before
start = time.time()
# ... old sequential code ...
old_time = time.time() - start

# After
start = time.time()
# ... new batch code ...
new_time = time.time() - start

print(f"Speedup: {old_time/new_time:.1f}x")
```

## Best Practices

### 1. Batch Size

```python
# Good: Process reasonable batches
if len(items) > 100:
    # Process in chunks
    for i in range(0, len(items), 100):
        chunk = items[i:i+100]
        results.extend(create_chat_completions_batch(chunk))
else:
    # Process all at once
    results = create_chat_completions_batch(items)
```

### 2. Error Handling

```python
# Always check for errors
results = create_chat_completions_batch(messages_list)

for i, result in enumerate(results):
    if "error" in result:
        print(f"Request {i} failed: {result['error']}")
        # Handle error (retry, use default, etc.)
    else:
        # Process successful result
        content = result["choices"][0]["message"]["content"]
```

### 3. Concurrency Tuning

```python
# Start conservative
results = create_chat_completions_batch(messages_list, max_workers=5)

# Monitor rate limits and adjust
# If no rate limit errors, increase:
results = create_chat_completions_batch(messages_list, max_workers=10)

# If hitting rate limits, decrease:
results = create_chat_completions_batch(messages_list, max_workers=3)
```

### 4. Backward Compatibility

Keep single-item functions for backward compatibility:

```python
def process_single(item):
    """Process a single item (backward compatible)."""
    results = process_batch([item])
    return results[0]

def process_batch(items):
    """Process multiple items (optimized)."""
    messages_list = [prepare_messages(item) for item in items]
    return create_chat_completions_batch(messages_list)
```

## Performance Expectations

| Batch Size | Sequential Time | Batch Time | Speedup |
|------------|----------------|------------|---------|
| 5 items    | ~5s            | ~1s        | 5x      |
| 10 items   | ~10s           | ~1.5s      | 6.7x    |
| 20 items   | ~20s           | ~2.5s      | 8x      |
| 50 items   | ~50s           | ~6s        | 8.3x    |
| 100 items  | ~100s          | ~12s       | 8.3x    |

*Note: Actual performance depends on API rate limits and network latency*

## Troubleshooting

### Rate Limit Errors

```python
# Reduce concurrency
results = create_chat_completions_batch(
    messages_list,
    max_workers=3  # Lower value
)

# Or process in smaller chunks
chunk_size = 20
for i in range(0, len(messages_list), chunk_size):
    chunk = messages_list[i:i+chunk_size]
    results.extend(create_chat_completions_batch(chunk))
    time.sleep(1)  # Small delay between chunks
```

### Memory Issues

```python
# Process in chunks for very large batches
def process_large_batch(messages_list, chunk_size=50):
    all_results = []
    for i in range(0, len(messages_list), chunk_size):
        chunk = messages_list[i:i+chunk_size]
        results = create_chat_completions_batch(chunk)
        all_results.extend(results)
    return all_results
```

### Timeout Errors

```python
# Reduce batch size or max_workers
results = create_chat_completions_batch(
    messages_list[:10],  # Smaller batch
    max_workers=5        # Lower concurrency
)
```

## Summary

The batch completions API provides significant performance improvements with minimal code changes. Focus on:

1. Identifying sequential LLM calls
2. Converting to batch processing
3. Testing with small batches first
4. Monitoring and tuning concurrency
5. Maintaining backward compatibility

Expected improvements: **5-10x faster processing** for bulk operations! 🚀
