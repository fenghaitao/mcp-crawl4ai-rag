"""
Utility functions for the Crawl4AI MCP server.
"""
import os
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
import json
from supabase import create_client, Client
from urllib.parse import urlparse
import openai
import re
import time

# Import CrossEncoder for reranking (lazy loading)
try:
    from sentence_transformers import CrossEncoder
except ImportError:
    print("!!! Error in importing CrossEncoder")
    CrossEncoder = None

# Import Copilot client
try:
    from .copilot_client import create_embeddings_batch_copilot, create_embedding_copilot, create_chat_completion_copilot
except ImportError:
    # Fallback for when running from different contexts (e.g., tests)
    from copilot_client import create_embeddings_batch_copilot, create_embedding_copilot, create_chat_completion_copilot

# Load OpenAI API key for embeddings
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global variable for Qwen embedding model (lazy loading)
_qwen_embedding_model = None

def get_qwen_embedding_model():
    """
    Get the Qwen embedding model (lazy loading).

    Returns:
        SentenceTransformer model or None if not available
    """
    global _qwen_embedding_model

    if _qwen_embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            # Force CPU usage
            device = "cpu"
            print(f"Loading Qwen embedding model on {device}...")

            # Load the model
            _qwen_embedding_model = SentenceTransformer(
                "Qwen/Qwen3-Embedding-0.6B",
                device=device,
                trust_remote_code=True
            )
            print("✓ Qwen embedding model loaded successfully")

        except Exception as e:
            print(f"Failed to load Qwen embedding model: {e}")
            _qwen_embedding_model = "failed"  # Mark as failed to avoid repeated attempts

    return _qwen_embedding_model if _qwen_embedding_model != "failed" else None

def create_embeddings_batch_qwen(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings using the local Qwen model.

    Args:
        texts: List of texts to create embeddings for

    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    if not texts:
        return []

    model = get_qwen_embedding_model()
    if model is None:
        print("Qwen model not available, returning zero embeddings")
        return [[0.0] * 1536 for _ in texts]  # Return default size embeddings

    try:
        print(f"Creating embeddings for {len(texts)} texts using Qwen model...")
        embeddings = model.encode(texts, convert_to_numpy=True)
        # Convert numpy arrays to lists
        return [embedding.tolist() for embedding in embeddings]
    except Exception as e:
        print(f"Error creating Qwen embeddings: {e}")
        return [[0.0] * 1536 for _ in texts]

def create_embedding_qwen(text: str) -> List[float]:
    """
    Create a single embedding using the local Qwen model.

    Args:
        text: Text to create an embedding for

    Returns:
        List of floats representing the embedding
    """
    embeddings = create_embeddings_batch_qwen([text])
    return embeddings[0] if embeddings else [0.0] * 1536

def get_supabase_client() -> Client:
    """
    Get a Supabase client with the URL and key from environment variables.

    Returns:
        Supabase client instance
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")

    return create_client(url, key)

def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for multiple texts in a single API call.
    Supports OpenAI, GitHub Copilot, and local Qwen embedding models.

    Args:
        texts: List of texts to create embeddings for

    Returns:
        List of embeddings (each embedding is a list of floats)
    """
    if not texts:
        return []

    # Check embedding preference order: Qwen -> Copilot -> OpenAI
    use_qwen = os.getenv("USE_QWEN_EMBEDDINGS", "false").lower() == "true"
    use_copilot = os.getenv("USE_COPILOT_EMBEDDINGS", "false").lower() == "true"

    if use_qwen:
        print("Using local Qwen model for embeddings...")
        try:
            return create_embeddings_batch_qwen(texts)
        except Exception as e:
            print(f"Error using Qwen embeddings: {e}")
            print("Falling back to next available option...")
            # Fall through to next option

    if use_copilot:
        print("Using GitHub Copilot for embeddings...")
        try:
            return create_embeddings_batch_copilot(texts)
        except Exception as e:
            print(f"Error using Copilot embeddings: {e}")
            print("Falling back to OpenAI embeddings...")
            # Fall through to OpenAI implementation

    # OpenAI implementation (fallback)
    print("Using OpenAI for embeddings...")
    max_retries = 3
    retry_delay = 1.0  # Start with 1 second delay

    for retry in range(max_retries):
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small", # Using text-embedding-3-small (same as Copilot)
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            if retry < max_retries - 1:
                print(f"Error creating batch embeddings (attempt {retry + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Failed to create batch embeddings after {max_retries} attempts: {e}")
                # Try creating embeddings one by one as fallback
                print("Attempting to create embeddings individually...")
                embeddings = []
                successful_count = 0

                for i, text in enumerate(texts):
                    try:
                        individual_response = openai.embeddings.create(
                            model="text-embedding-3-small",
                            input=[text]
                        )
                        embeddings.append(individual_response.data[0].embedding)
                        successful_count += 1
                    except Exception as individual_error:
                        print(f"Failed to create embedding for text {i}: {individual_error}")
                        # Add zero embedding as fallback
                        embeddings.append([0.0] * 1536)

                print(f"Successfully created {successful_count}/{len(texts)} embeddings individually")
                return embeddings

def create_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 200,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a chat completion using either OpenAI or GitHub Copilot.
    Supports both OpenAI and GitHub Copilot chat APIs.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use (if None, uses MODEL_CHOICE env var)
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters

    Returns:
        Chat completion response
    """
    # Check if we should use Copilot for chat completions
    use_copilot = os.getenv("USE_COPILOT_CHAT", "false").lower() == "true"

    # Get model choice from environment if not specified
    if model is None:
        model = os.getenv("MODEL_CHOICE", "gpt-4o-mini")

    if use_copilot:
        print("Using GitHub Copilot for chat completion...")
        try:
            # Map common OpenAI model names to Copilot equivalents
            copilot_model = model
            if "gpt-4o-mini" in model or "gpt-4.1-nano" in model:
                copilot_model = "gpt-4o"  # Copilot's equivalent

            return create_chat_completion_copilot(
                messages=messages,
                model=copilot_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except Exception as e:
            print(f"Error using Copilot for chat completion: {e}")
            print("Falling back to OpenAI...")
            # Fall through to OpenAI implementation

    # OpenAI implementation
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Convert OpenAI response to dictionary for consistency
        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content,
                        "role": response.choices[0].message.role
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
            ],
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }
    except Exception as e:
        print(f"Error creating chat completion: {e}")
        raise


def create_embedding(text: str) -> List[float]:
    """
    Create an embedding for a single text.
    Supports OpenAI, GitHub Copilot, and local Qwen embedding models.

    Args:
        text: Text to create an embedding for

    Returns:
        List of floats representing the embedding
    """
    # Check embedding preference order: Qwen -> Copilot -> OpenAI
    use_qwen = os.getenv("USE_QWEN_EMBEDDINGS", "false").lower() == "true"
    use_copilot = os.getenv("USE_COPILOT_EMBEDDINGS", "false").lower() == "true"

    if use_qwen:
        try:
            return create_embedding_qwen(text)
        except Exception as e:
            print(f"Error using Qwen for single embedding: {e}")
            print("Falling back to batch method...")
            # Fall through to batch method

    if use_copilot:
        try:
            return create_embedding_copilot(text)
        except Exception as e:
            print(f"Error using Copilot for single embedding: {e}")
            print("Falling back to batch method...")
            # Fall through to batch method

    try:
        embeddings = create_embeddings_batch([text])
        return embeddings[0] if embeddings else [0.0] * 1536
    except Exception as e:
        print(f"Error creating embedding: {e}")
        # Return empty embedding if there's an error
        return [0.0] * 1536

def generate_contextual_embedding(full_document: str, chunk: str) -> Tuple[str, bool]:
    """
    Generate contextual information for a chunk within a document to improve retrieval.

    Args:
        full_document: The complete document text
        chunk: The specific chunk of text to generate context for

    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    model_choice = os.getenv("MODEL_CHOICE")

    try:
        # Create the prompt for generating contextual information
        prompt = f"""<document>
{full_document[:25000]}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{chunk}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        # Call the chat completion API to generate contextual information
        response = create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise contextual information."},
                {"role": "user", "content": prompt}
            ],
            model=model_choice,
            temperature=0.3,
            max_tokens=200
        )

        # Extract the generated context
        context = response["choices"][0]["message"]["content"].strip()

        # Combine the context with the original chunk
        contextual_text = f"{context}\n---\n{chunk}"

        return contextual_text, True

    except Exception as e:
        print(f"Error generating contextual embedding: {e}. Using original chunk instead.")
        return chunk, False

def process_chunk_with_context(args):
    """
    Process a single chunk with contextual embedding.
    This function is designed to be used with concurrent.futures.

    Args:
        args: Tuple containing (url, content, full_document)

    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    url, content, full_document = args
    return generate_contextual_embedding(full_document, content)

def add_documents_to_supabase(
    client: Client,
    urls: List[str],
    chunk_numbers: List[int],
    contents: List[str],
    metadatas: List[Dict[str, Any]],
    url_to_full_document: Dict[str, str],
    delete_existing: bool = True,
    batch_size: int = 20
) -> None:
    """
    Add documents to the Supabase crawled_pages table in batches.
    Deletes existing records with the same URLs before inserting to prevent duplicates.

    Args:
        client: Supabase client
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        contents: List of document contents
        metadatas: List of document metadata
        url_to_full_document: Dictionary mapping URLs to their full document content
        batch_size: Size of each batch for insertion
    """
    # Delete existing records only if delete_existing is True
    if delete_existing:
        # Get unique URLs to delete existing records
        unique_urls = list(set(urls))

        # Delete existing records for these URLs in a single operation
        try:
            if unique_urls:
                # Use the .in_() filter to delete all records with matching URLs
                client.table("crawled_pages").delete().in_("url", unique_urls).execute()
        except Exception as e:
            print(f"Batch delete failed: {e}. Trying one-by-one deletion as fallback.")
            # Fallback: delete records one by one
            for url in unique_urls:
                try:
                    client.table("crawled_pages").delete().eq("url", url).execute()
                except Exception as inner_e:
                    print(f"Error deleting record for URL {url}: {inner_e}")
                    # Continue with the next URL even if one fails
    else:
        print("Skipping deletion of existing records (--skip-delete enabled)")

    # Check if MODEL_CHOICE is set for contextual embeddings
    use_contextual_embeddings = os.getenv("USE_CONTEXTUAL_EMBEDDINGS", "false") == "true"
    print(f"\n\nUse contextual embeddings: {use_contextual_embeddings}\n\n")

    # Process in batches to avoid memory issues
    for i in range(0, len(contents), batch_size):
        batch_end = min(i + batch_size, len(contents))

        # Get batch slices
        batch_urls = urls[i:batch_end]
        batch_chunk_numbers = chunk_numbers[i:batch_end]
        batch_contents = contents[i:batch_end]
        batch_metadatas = metadatas[i:batch_end]

        # Apply contextual embedding to each chunk if MODEL_CHOICE is set
        if use_contextual_embeddings:
            # Prepare arguments for parallel processing
            process_args = []
            for j, content in enumerate(batch_contents):
                url = batch_urls[j]
                full_document = url_to_full_document.get(url, "")
                process_args.append((url, content, full_document))

            # Process in parallel using ThreadPoolExecutor
            contextual_contents = [None] * len(batch_contents)
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all tasks and collect results
                future_to_idx = {executor.submit(process_chunk_with_context, arg): idx
                                for idx, arg in enumerate(process_args)}

                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        result, success = future.result()
                        contextual_contents[idx] = result
                        if success:
                            batch_metadatas[idx]["contextual_embedding"] = True
                    except Exception as e:
                        print(f"Error processing chunk {idx}: {e}")
                        # Use original content as fallback
                        contextual_contents[idx] = batch_contents[idx]

            # Ensure all positions are filled; fall back to original content where needed
            for j in range(len(contextual_contents)):
                if contextual_contents[j] is None:
                    contextual_contents[j] = batch_contents[j]
        else:
            # If not using contextual embeddings, use original contents
            contextual_contents = batch_contents

        # Create embeddings for the entire batch at once
        batch_embeddings = create_embeddings_batch(contextual_contents)

        batch_data = []
        for j in range(len(contextual_contents)):
            # Extract metadata fields
            chunk_size = len(contextual_contents[j])

            # Use source_id from metadata if available, otherwise extract from URL
            source_id = batch_metadatas[j].get("source_id")
            if not source_id:
                parsed_url = urlparse(batch_urls[j])
                source_id = parsed_url.netloc or parsed_url.path

            # Prepare data for insertion
            data = {
                "url": batch_urls[j],
                "chunk_number": batch_chunk_numbers[j],
                "content": contextual_contents[j],  # Store original content
                "metadata": {
                    "chunk_size": chunk_size,
                    **batch_metadatas[j]
                },
                "source_id": source_id,  # Add source_id field
                "embedding": batch_embeddings[j]  # Use embedding from contextual content
            }

            batch_data.append(data)

        # Insert batch into Supabase with retry logic
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second delay

        for retry in range(max_retries):
            try:
                if delete_existing:
                    # Normal insert (we already deleted existing records)
                    client.table("crawled_pages").insert(batch_data).execute()
                else:
                    # Upsert - insert or update on conflict using unique constraint
                    # Use on_conflict parameter to specify which columns to use for conflict resolution
                    client.table("crawled_pages").upsert(batch_data, on_conflict="url,chunk_number").execute()
                # Success - break out of retry loop
                break
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"Error inserting batch into Supabase (attempt {retry + 1}/{max_retries}): {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Final attempt failed
                    print(f"Failed to insert batch after {max_retries} attempts: {e}")
                    # Optionally, try inserting records one by one as a last resort
                    print("Attempting to insert records individually...")
                    successful_inserts = 0
                    for record in batch_data:
                        try:
                            if delete_existing:
                                client.table("crawled_pages").insert(record).execute()
                            else:
                                client.table("crawled_pages").upsert(record, on_conflict="url,chunk_number").execute()
                            successful_inserts += 1
                        except Exception as individual_error:
                            print(f"Failed to insert individual record for URL {record['url']}: {individual_error}")

                    if successful_inserts > 0:
                        print(f"Successfully inserted {successful_inserts}/{len(batch_data)} records individually")

def search_documents(
    client: Client,
    query: str,
    match_count: int = 10,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents in Supabase using vector similarity.

    Args:
        client: Supabase client
        query: Query text
        match_count: Maximum number of results to return
        filter_metadata: Optional metadata filter

    Returns:
        List of matching documents
    """
    # Create embedding for the query
    query_embedding = create_embedding(query)

    # Execute the search using the match_crawled_pages function
    try:
        # Only include filter parameter if filter_metadata is provided and not empty
        params = {
            'query_embedding': query_embedding,
            'match_count': match_count
        }

        # Only add the filter if it's actually provided and not empty
        if filter_metadata:
            params['filter'] = filter_metadata  # Pass the dictionary directly, not JSON-encoded

        result = client.rpc('match_crawled_pages', params).execute()

        return result.data
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []


def extract_code_blocks(markdown_content: str, min_length: int = 1000) -> List[Dict[str, Any]]:
    """
    Extract code blocks from markdown content along with context.

    Args:
        markdown_content: The markdown content to extract code blocks from
        min_length: Minimum length of code blocks to extract (default: 1000 characters)

    Returns:
        List of dictionaries containing code blocks and their context
    """
    code_blocks = []

    # Skip if content starts with triple backticks (edge case for files wrapped in backticks)
    content = markdown_content.strip()
    start_offset = 0
    if content.startswith('```'):
        # Skip the first triple backticks
        start_offset = 3
        print("Skipping initial triple backticks")

    # Find all occurrences of triple backticks
    backtick_positions = []
    pos = start_offset
    while True:
        pos = markdown_content.find('```', pos)
        if pos == -1:
            break
        backtick_positions.append(pos)
        pos += 3

    # Process pairs of backticks
    i = 0
    while i < len(backtick_positions) - 1:
        start_pos = backtick_positions[i]
        end_pos = backtick_positions[i + 1]

        # Extract the content between backticks
        code_section = markdown_content[start_pos+3:end_pos]

        # Check if there's a language specifier on the first line
        lines = code_section.split('\n', 1)
        if len(lines) > 1:
            # Check if first line is a language specifier (no spaces, common language names)
            first_line = lines[0].strip()
            if first_line and not ' ' in first_line and len(first_line) < 20:
                language = first_line
                code_content = lines[1].strip() if len(lines) > 1 else ""
            else:
                language = ""
                code_content = code_section.strip()
        else:
            language = ""
            code_content = code_section.strip()

        # Skip if code block is too short
        if len(code_content) < min_length:
            i += 2  # Move to next pair
            continue

        # Extract context before (1000 chars)
        context_start = max(0, start_pos - 1000)
        context_before = markdown_content[context_start:start_pos].strip()

        # Extract context after (1000 chars)
        context_end = min(len(markdown_content), end_pos + 3 + 1000)
        context_after = markdown_content[end_pos + 3:context_end].strip()

        code_blocks.append({
            'code': code_content,
            'language': language,
            'context_before': context_before,
            'context_after': context_after,
            'full_context': f"{context_before}\n\n{code_content}\n\n{context_after}"
        })

        # Move to next pair (skip the closing backtick we just processed)
        i += 2

    return code_blocks


def generate_code_example_summary(code: str, context_before: str, context_after: str) -> str:
    """
    Generate a summary for a code example using its surrounding context.

    Args:
        code: The code example
        context_before: Context before the code
        context_after: Context after the code

    Returns:
        A summary of what the code example demonstrates
    """
    model_choice = os.getenv("MODEL_CHOICE")

    # Create the prompt
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


def add_code_examples_to_supabase(
    client: Client,
    urls: List[str],
    chunk_numbers: List[int],
    code_examples: List[str],
    summaries: List[str],
    metadatas: List[Dict[str, Any]],
    delete_existing: bool = True,
    batch_size: int = 20
):
    """
    Add code examples to the Supabase code_examples table in batches.

    Args:
        client: Supabase client
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        code_examples: List of code example contents
        summaries: List of code example summaries
        metadatas: List of metadata dictionaries
        batch_size: Size of each batch for insertion
    """
    if not urls:
        return

    # Delete existing records for these URLs only if delete_existing is True
    if delete_existing:
        unique_urls = list(set(urls))
        for url in unique_urls:
            try:
                client.table('code_examples').delete().eq('url', url).execute()
            except Exception as e:
                print(f"Error deleting existing code examples for {url}: {e}")
    else:
        print("Skipping deletion of existing code examples (--skip-delete enabled)")

    # Process in batches
    total_items = len(urls)
    for i in range(0, total_items, batch_size):
        batch_end = min(i + batch_size, total_items)
        batch_texts = []

        # Create combined texts for embedding (code + summary)
        for j in range(i, batch_end):
            combined_text = f"{code_examples[j]}\n\nSummary: {summaries[j]}"
            batch_texts.append(combined_text)

        # Create embeddings for the batch
        embeddings = create_embeddings_batch(batch_texts)

        # Check if embeddings are valid (not all zeros)
        valid_embeddings = []
        for embedding in embeddings:
            if embedding and not all(v == 0.0 for v in embedding):
                valid_embeddings.append(embedding)
            else:
                print(f"Warning: Zero or invalid embedding detected, creating new one...")
                # Try to create a single embedding as fallback
                single_embedding = create_embedding(batch_texts[len(valid_embeddings)])
                valid_embeddings.append(single_embedding)

        # Prepare batch data
        batch_data = []
        for j, embedding in enumerate(valid_embeddings):
            idx = i + j

            # Use source_id from metadata if available, otherwise extract from URL
            source_id = metadatas[idx].get("source_id")
            if not source_id:
                parsed_url = urlparse(urls[idx])
                source_id = parsed_url.netloc or parsed_url.path

            batch_data.append({
                'url': urls[idx],
                'chunk_number': chunk_numbers[idx],
                'content': code_examples[idx],
                'summary': summaries[idx],
                'metadata': metadatas[idx],  # Store as JSON object, not string
                'source_id': source_id,
                'embedding': embedding
            })

        # Insert batch into Supabase with retry logic
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second delay

        for retry in range(max_retries):
            try:
                if delete_existing:
                    # Normal insert (we already deleted existing records)
                    client.table('code_examples').insert(batch_data).execute()
                else:
                    # Upsert - insert or update on conflict using unique constraint
                    client.table('code_examples').upsert(batch_data, on_conflict="url,chunk_number").execute()
                # Success - break out of retry loop
                break
            except Exception as e:
                if retry < max_retries - 1:
                    print(f"Error inserting batch into Supabase (attempt {retry + 1}/{max_retries}): {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Final attempt failed
                    print(f"Failed to insert batch after {max_retries} attempts: {e}")
                    # Optionally, try inserting records one by one as a last resort
                    print("Attempting to insert records individually...")
                    successful_inserts = 0
                    for record in batch_data:
                        try:
                            if delete_existing:
                                client.table('code_examples').insert(record).execute()
                            else:
                                client.table('code_examples').upsert(record, on_conflict="url,chunk_number").execute()
                            successful_inserts += 1
                        except Exception as individual_error:
                            print(f"Failed to insert individual record for URL {record['url']}: {individual_error}")

                    if successful_inserts > 0:
                        print(f"Successfully inserted {successful_inserts}/{len(batch_data)} records individually")
        print(f"Inserted batch {i//batch_size + 1} of {(total_items + batch_size - 1)//batch_size} code examples")


def update_source_info(client: Client, source_id: str, summary: str, word_count: int):
    """
    Update or insert source information in the sources table.

    Args:
        client: Supabase client
        source_id: The source ID (domain)
        summary: Summary of the source
        word_count: Total word count for the source
    """
    try:
        # Try to update existing source
        result = client.table('sources').update({
            'summary': summary,
            'total_word_count': word_count,
            'updated_at': 'now()'
        }).eq('source_id', source_id).execute()

        # If no rows were updated, insert new source
        if not result.data:
            client.table('sources').insert({
                'source_id': source_id,
                'summary': summary,
                'total_word_count': word_count
            }).execute()
            print(f"Created new source: {source_id}")
        else:
            print(f"Updated source: {source_id}")

    except Exception as e:
        print(f"Error updating source {source_id}: {e}")


def extract_source_summary(source_id: str, content: str, max_length: int = 500) -> str:
    """
    Extract a summary for a source from its content using an LLM.

    This function uses the OpenAI API to generate a concise summary of the source content.

    Args:
        source_id: The source ID (domain)
        content: The content to extract a summary from
        max_length: Maximum length of the summary

    Returns:
        A summary string
    """
    # Default summary if we can't extract anything meaningful
    default_summary = f"Content from {source_id}"

    if not content or len(content.strip()) == 0:
        return default_summary

    # Get the model choice from environment variables
    model_choice = os.getenv("MODEL_CHOICE")

    # Limit content length to avoid token limits
    truncated_content = content[:25000] if len(content) > 25000 else content

    # Create the prompt for generating the summary
    prompt = f"""<source_content>
{truncated_content}
</source_content>

The above content is from the documentation for '{source_id}'. Please provide a concise summary (3-5 sentences) that describes what this library/tool/framework is about. The summary should help understand what the library/tool/framework accomplishes and the purpose.
"""

    try:
        # Call the chat completion API to generate the summary
        response = create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides concise library/tool/framework summaries."},
                {"role": "user", "content": prompt}
            ],
            model=model_choice,
            temperature=0.3,
            max_tokens=150
        )

        # Extract the generated summary
        summary = response["choices"][0]["message"]["content"].strip()

        # Ensure the summary is not too long
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    except Exception as e:
        print(f"Error generating summary with LLM for {source_id}: {e}. Using default summary.")
        return default_summary


def search_code_examples(
    client: Client,
    query: str,
    match_count: int = 10,
    filter_metadata: Optional[Dict[str, Any]] = None,
    source_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for code examples in Supabase using vector similarity.

    Args:
        client: Supabase client
        query: Query text
        match_count: Maximum number of results to return
        filter_metadata: Optional metadata filter
        source_id: Optional source ID to filter results

    Returns:
        List of matching code examples
    """
    # Create a more descriptive query for better embedding match
    # Since code examples are embedded with their summaries, we should make the query more descriptive
    enhanced_query = f"Code example for {query}\n\nSummary: Example code showing {query}"

    # Create embedding for the enhanced query
    query_embedding = create_embedding(enhanced_query)

    # Execute the search using the match_code_examples function
    try:
        # Only include filter parameter if filter_metadata is provided and not empty
        params = {
            'query_embedding': query_embedding,
            'match_count': match_count
        }

        # Only add the filter if it's actually provided and not empty
        if filter_metadata:
            params['filter'] = filter_metadata

        # Add source filter if provided
        if source_id:
            params['source_filter'] = source_id

        result = client.rpc('match_code_examples', params).execute()

        return result.data
    except Exception as e:
        print(f"Error searching code examples: {e}")
        return []


def get_rerank_model():
    # Initialize reranking model if enabled
    reranking_model = None
    reranking_model_name = None
    if os.getenv("USE_RERANKING", "false") == "true":
        # Check which reranker model to use
        use_qwen_reranker = os.getenv("USE_QWEN_RERANKER", "false").lower() == "true"

        if use_qwen_reranker:
            try:
                print("Loading Qwen reranker model...")
                reranking_model = CrossEncoder("Qwen/Qwen3-Reranker-0.6B", device="cpu", trust_remote_code=True)
                reranking_model_name = "Qwen/Qwen3-Reranker-0.6B"
                print("✓ Qwen reranker model loaded successfully")
            except Exception as e:
                print(f"Failed to load Qwen reranker model: {e}")
                print("Falling back to CrossEncoder model...")
                try:
                    reranking_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                    reranking_model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
                    print("✓ CrossEncoder fallback model loaded successfully")
                except Exception as fallback_e:
                    print(f"Failed to load fallback reranking model: {fallback_e}")
                    reranking_model = None
        else:
            try:
                print("Loading CrossEncoder reranker model...")
                reranking_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                reranking_model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
                print("✓ CrossEncoder reranker model loaded successfully")
            except Exception as e:
                print(f"Failed to load CrossEncoder reranking model: {e}")
                reranking_model = None
    return reranking_model


def combine_hybrid_results(vector_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combine vector and keyword search results with preference for items appearing in both.

    Args:
        vector_results: Results from vector search
        keyword_results: Results from keyword search

    Returns:
        Combined and deduplicated results
    """
    seen_ids = set()
    combined_results = []

    # First, add items that appear in both searches (these are the best matches)
    vector_ids = {r.get('id') for r in vector_results if r.get('id')}
    both_searches_count = 0

    for kr in keyword_results:
        if kr.get('id') in vector_ids and kr.get('id') not in seen_ids:
            # Find the vector result to get similarity score
            for vr in vector_results:
                if vr.get('id') == kr.get('id'):
                    # Boost similarity score for items in both results
                    vr['similarity'] = min(1.0, vr.get('similarity', 0) * 1.2)
                    combined_results.append(vr)
                    seen_ids.add(kr.get('id'))
                    both_searches_count += 1
                    break

    # Then add remaining vector results (semantic matches without exact keyword)
    vector_only_count = 0
    for vr in vector_results:
        if vr.get('id') and vr['id'] not in seen_ids:
            combined_results.append(vr)
            seen_ids.add(vr['id'])
            vector_only_count += 1

    # Finally, add pure keyword matches if needed
    keyword_only_count = 0
    for kr in keyword_results:
        if kr.get('id') not in seen_ids:
            # Convert keyword result to match vector result format
            combined_results.append({
                'id': kr.get('id'),
                'url': kr.get('url'),
                'chunk_number': kr.get('chunk_number'),
                'content': kr.get('content'),
                'metadata': kr.get('metadata'),
                'source_id': kr.get('source_id'),
                'similarity': 0.5  # Default similarity for keyword-only matches
            })
            seen_ids.add(kr.get('id'))
            keyword_only_count += 1

    # Sort by similarity score
    combined_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)

    print(f"      📊 Hybrid combination: {both_searches_count} both + {vector_only_count} vector + {keyword_only_count} keyword")

    return combined_results

def execute_multi_source_search(
    supabase_client: Client,
    query: str,
    source_ids: List[str],
    match_count: int,
    use_hybrid_search: bool
) -> List[Dict[str, Any]]:
    """
    Execute search across multiple sources and combine results.

    Args:
        supabase_client: Supabase client
        query: Search query
        source_ids: List of source IDs to search
        match_count: Number of results to return
        use_hybrid_search: Whether to use hybrid search

    Returns:
        Combined search results from all sources
    """
    all_results = []

    for source_id in source_ids:
        source_filter = {"source_id": source_id}
        print(f"   🎯 Querying source: {source_id}")

        if use_hybrid_search:
            # Vector search for this source
            vector_results = search_documents(
                client=supabase_client,
                query=query,
                match_count=match_count,
                filter_metadata=source_filter
            )

            # Keyword search for this source
            keyword_query = supabase_client.from_('crawled_pages')\
                .select('id, url, chunk_number, content, metadata, source_id')\
                .ilike('content', f'%{query}%')\
                .eq('source_id', source_id)\
                .limit(match_count)

            keyword_response = keyword_query.execute()
            keyword_results = keyword_response.data if keyword_response.data else []

            # Combine for this source
            source_results = combine_hybrid_results(vector_results, keyword_results)
        else:
            # Standard vector search for this source
            source_results = search_documents(
                client=supabase_client,
                query=query,
                match_count=match_count,
                filter_metadata=source_filter
            )

        all_results.extend(source_results)
        print(f"      ✅ Found {len(source_results)} results from {source_id}")

    # Sort all results by similarity and take top results
    all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    final_results = all_results[:match_count]
    print(f"   🔗 Combined results: {len(final_results)} total from {len(source_ids)} sources")

    return final_results

def rerank_results(model: CrossEncoder, query: str, results: List[Dict[str, Any]], content_key: str = "content") -> List[Dict[str, Any]]:
    """
    Rerank search results using a cross-encoder model.

    Args:
        model: The cross-encoder model to use for reranking
        query: The search query
        results: List of search results
        content_key: The key in each result dict that contains the text content

    Returns:
        Reranked list of results
    """
    if not model or not results:
        return results

    try:
        # Extract content from results
        texts = [result.get(content_key, "") for result in results]

        # Create pairs of [query, document] for the cross-encoder
        pairs = [[query, text] for text in texts]

        # Get relevance scores from the cross-encoder
        scores = model.predict(pairs)

        # Add scores to results and sort by score (descending)
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])

        # Sort by rerank score
        reranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)

        return reranked
    except Exception as e:
        print(f"Error during reranking: {e}")
        return results
