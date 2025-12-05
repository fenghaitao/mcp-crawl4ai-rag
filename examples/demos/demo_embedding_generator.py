"""
Demo script for EmbeddingGenerator.

Demonstrates the usage of the EmbeddingGenerator class for generating
embeddings for document chunks.
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from user_manual_chunker import (
    MarkdownParser,
    SemanticChunkerImpl,
    EmbeddingGenerator,
)


def main():
    """Demonstrate EmbeddingGenerator functionality."""
    
    print("=" * 70)
    print("EmbeddingGenerator Demo")
    print("=" * 70)
    
    # Sample markdown document with code
    sample_doc = """# Introduction to Python

Python is a high-level programming language.

## Basic Syntax

Here's a simple example:

```python
def hello_world():
    print("Hello, World!")
```

The function above prints a greeting message.

## Variables

Variables in Python are dynamically typed:

```python
x = 10
name = "Alice"
```

You can assign values without declaring types.
"""
    
    print("\n1. Parsing sample document...")
    parser = MarkdownParser()
    doc_structure = parser.parse(sample_doc, source_path="demo.md")
    print(f"   ✓ Parsed document with {len(doc_structure.headings)} headings")
    print(f"   ✓ Found {len(doc_structure.code_blocks)} code blocks")
    
    print("\n2. Chunking document...")
    chunker = SemanticChunkerImpl(
        max_chunk_size=500,
        min_chunk_size=50,
        chunk_overlap=0
    )
    chunks = chunker.chunk_document(doc_structure)
    print(f"   ✓ Created {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"   - Chunk {i+1}: {len(chunk.content)} chars, "
              f"lines {chunk.line_start}-{chunk.line_end}")
    
    print("\n3. Initializing EmbeddingGenerator...")
    embedding_gen = EmbeddingGenerator(
        model="text-embedding-3-small",
        batch_size=32,
        normalize=True
    )
    print(f"   ✓ Model: {embedding_gen.model}")
    print(f"   ✓ Batch size: {embedding_gen.batch_size}")
    print(f"   ✓ Normalization: {embedding_gen.normalize}")
    
    print("\n4. Generating embeddings (batch)...")
    try:
        embeddings = embedding_gen.generate_embeddings(chunks)
        print(f"   ✓ Generated {len(embeddings)} embeddings")
        
        for i, emb in enumerate(embeddings):
            norm = np.linalg.norm(emb)
            print(f"   - Embedding {i+1}: shape={emb.shape}, "
                  f"dtype={emb.dtype}, L2 norm={norm:.6f}")
            
            # Verify normalization
            if embedding_gen.normalize:
                if abs(norm - 1.0) < 1e-5:
                    print(f"     ✓ Vector is normalized (L2 norm ≈ 1.0)")
                else:
                    print(f"     ✗ Vector is NOT normalized (L2 norm = {norm})")
        
        # Show sample embedding values
        print(f"\n   Sample embedding values (first 10 dimensions):")
        print(f"   {embeddings[0][:10]}")
        
    except Exception as e:
        print(f"   ✗ Error generating embeddings: {e}")
        print(f"   Note: This requires GITHUB_TOKEN to be set for Copilot API")
        return
    
    print("\n5. Testing single embedding generation...")
    try:
        single_embedding = embedding_gen.generate_embedding_single(chunks[0])
        norm = np.linalg.norm(single_embedding)
        print(f"   ✓ Generated single embedding: shape={single_embedding.shape}, "
              f"L2 norm={norm:.6f}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n6. Testing code syntax preservation...")
    # Find a chunk with code
    code_chunk = None
    for chunk in chunks:
        if "```" in chunk.content:
            code_chunk = chunk
            break
    
    if code_chunk:
        print(f"   ✓ Found chunk with code block")
        print(f"   Content preview:")
        preview = code_chunk.content[:200].replace('\n', '\n   ')
        print(f"   {preview}...")
        
        # Verify code syntax is preserved in embedding input
        prepared_text = embedding_gen._prepare_text_for_embedding(code_chunk)
        if "```" in prepared_text:
            print(f"   ✓ Code syntax markers preserved in embedding input")
        else:
            print(f"   ✗ Code syntax markers NOT preserved")
    else:
        print(f"   - No code chunks found in this example")
    
    print("\n7. Testing batch processing efficiency...")
    # Create multiple chunks for batch testing
    large_doc = sample_doc * 5  # Repeat document
    doc_structure_large = parser.parse(large_doc, source_path="demo_large.md")
    chunks_large = chunker.chunk_document(doc_structure_large)
    
    print(f"   Processing {len(chunks_large)} chunks...")
    try:
        import time
        start_time = time.time()
        embeddings_large = embedding_gen.generate_embeddings(chunks_large)
        elapsed = time.time() - start_time
        
        print(f"   ✓ Generated {len(embeddings_large)} embeddings in {elapsed:.2f}s")
        print(f"   ✓ Average: {elapsed/len(embeddings_large):.3f}s per embedding")
        
        # Verify all embeddings are normalized
        all_normalized = all(
            abs(np.linalg.norm(emb) - 1.0) < 1e-5 
            for emb in embeddings_large
        )
        if all_normalized:
            print(f"   ✓ All embeddings are properly normalized")
        else:
            print(f"   ✗ Some embeddings are not normalized")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print("\nKey features demonstrated:")
    print("  ✓ Batch embedding generation")
    print("  ✓ Single embedding generation")
    print("  ✓ Code syntax preservation")
    print("  ✓ Vector normalization for cosine similarity")
    print("  ✓ Integration with existing Copilot infrastructure")


if __name__ == "__main__":
    main()
