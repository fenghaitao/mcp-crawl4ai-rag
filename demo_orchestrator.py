#!/usr/bin/env python3
"""
Demo script for UserManualChunker orchestrator.

Tests the complete pipeline: parsing, chunking, metadata extraction,
summary generation, and embedding generation.
"""

import sys
import json
from pathlib import Path

from src.user_manual_chunker import (
    UserManualChunker,
    ChunkerConfig
)


def demo_single_document():
    """Demo processing a single document."""
    print("=" * 80)
    print("Demo: Processing Single Document")
    print("=" * 80)
    
    # Find a sample document
    sample_docs = [
        "pipeline_output/downloaded_pages/simics_docs_dml-1.4-reference-manual_introduction.md",
        "pipeline_output/downloaded_pages/simics_docs_dml-1.4-reference-manual_language.md",
    ]
    
    sample_doc = None
    for doc in sample_docs:
        if Path(doc).exists():
            sample_doc = doc
            break
    
    if not sample_doc:
        print("No sample documents found. Skipping demo.")
        return
    
    print(f"\nProcessing: {sample_doc}")
    
    # Create configuration
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        chunk_overlap=50,
        generate_summaries=False,  # Skip summaries for faster demo
        generate_embeddings=False  # Skip embeddings for faster demo
    )
    
    # Create orchestrator
    chunker = UserManualChunker.from_config(config)
    
    # Process document
    try:
        chunks = chunker.process_document(
            sample_doc,
            generate_embeddings=False,
            generate_summaries=False
        )
        
        print(f"\n✓ Successfully processed document")
        print(f"  - Created {len(chunks)} chunks")
        
        # Show first chunk
        if chunks:
            print(f"\nFirst chunk:")
            print(f"  - ID: {chunks[0].chunk_id}")
            print(f"  - Size: {chunks[0].metadata.char_count} characters")
            print(f"  - Heading: {' > '.join(chunks[0].metadata.heading_hierarchy)}")
            print(f"  - Contains code: {chunks[0].metadata.contains_code}")
            if chunks[0].metadata.code_languages:
                print(f"  - Languages: {', '.join(chunks[0].metadata.code_languages)}")
            print(f"\n  Content preview (first 200 chars):")
            print(f"  {chunks[0].content[:200]}...")
        
        # Show statistics
        stats = chunker.get_statistics()
        print(f"\nStatistics:")
        print(f"  - Total chunks: {stats['total_chunks']}")
        print(f"  - Chunks with code: {stats['total_code_blocks']}")
        print(f"  - Average chunk size: {stats['average_chunk_size']:.1f} chars")
        print(f"  - Processing time: {stats['processing_time_seconds']:.2f}s")
        
        return chunks
        
    except Exception as e:
        print(f"\n✗ Error processing document: {e}")
        import traceback
        traceback.print_exc()
        return None


def demo_json_export(chunks):
    """Demo JSON export functionality."""
    print("\n" + "=" * 80)
    print("Demo: JSON Export")
    print("=" * 80)
    
    if not chunks:
        print("No chunks to export. Skipping demo.")
        return
    
    # Create orchestrator for export
    config = ChunkerConfig()
    chunker = UserManualChunker.from_config(config)
    
    # Export to JSON
    output_path = "demo_output_orchestrator.json"
    
    try:
        chunker.export_to_json(chunks, output_path, include_statistics=True)
        print(f"\n✓ Successfully exported to {output_path}")
        
        # Show file size
        file_size = Path(output_path).stat().st_size
        print(f"  - File size: {file_size:,} bytes")
        
        # Load and show structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        print(f"  - Chunks in file: {len(data['chunks'])}")
        print(f"  - Has statistics: {'statistics' in data}")
        
        # Show first chunk structure
        if data['chunks']:
            first_chunk = data['chunks'][0]
            print(f"\n  First chunk structure:")
            print(f"    - chunk_id: {first_chunk['chunk_id']}")
            print(f"    - content length: {len(first_chunk['content'])} chars")
            print(f"    - metadata keys: {list(first_chunk['metadata'].keys())}")
            print(f"    - has summary: {first_chunk['summary'] is not None}")
            print(f"    - has embedding: {first_chunk['embedding'] is not None}")
        
    except Exception as e:
        print(f"\n✗ Error exporting to JSON: {e}")
        import traceback
        traceback.print_exc()


def demo_vector_db_export(chunks):
    """Demo vector database format export."""
    print("\n" + "=" * 80)
    print("Demo: Vector Database Format Export")
    print("=" * 80)
    
    if not chunks:
        print("No chunks to export. Skipping demo.")
        return
    
    # Create orchestrator for export
    config = ChunkerConfig()
    chunker = UserManualChunker.from_config(config)
    
    # Export to vector DB format
    output_path = "demo_output_vector_db.json"
    
    try:
        chunker.export_to_vector_db_format(chunks, output_path)
        print(f"\n✓ Successfully exported to {output_path}")
        
        # Show file size
        file_size = Path(output_path).stat().st_size
        print(f"  - File size: {file_size:,} bytes")
        
        # Load and show structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        print(f"  - Records in file: {len(data)}")
        
        # Show first record structure
        if data:
            first_record = data[0]
            print(f"\n  First record structure:")
            print(f"    - id: {first_record['id']}")
            print(f"    - content length: {len(first_record['content'])} chars")
            print(f"    - metadata keys: {list(first_record['metadata'].keys())}")
            print(f"    - has summary: {first_record['summary'] is not None}")
            print(f"    - has embedding: {first_record['embedding'] is not None}")
        
    except Exception as e:
        print(f"\n✗ Error exporting to vector DB format: {e}")
        import traceback
        traceback.print_exc()


def demo_directory_processing():
    """Demo processing multiple documents in a directory."""
    print("\n" + "=" * 80)
    print("Demo: Directory Processing")
    print("=" * 80)
    
    # Check if directory exists
    directory = "pipeline_output/downloaded_pages"
    
    if not Path(directory).exists():
        print(f"Directory not found: {directory}")
        print("Skipping demo.")
        return
    
    print(f"\nProcessing directory: {directory}")
    print(f"Pattern: *.md (first 3 files only for demo)")
    
    # Create configuration
    config = ChunkerConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        chunk_overlap=50,
        generate_summaries=False,
        generate_embeddings=False
    )
    
    # Create orchestrator
    chunker = UserManualChunker.from_config(config)
    
    # Find first 3 markdown files
    md_files = list(Path(directory).glob("*.md"))[:3]
    
    if not md_files:
        print("No markdown files found. Skipping demo.")
        return
    
    print(f"\nProcessing {len(md_files)} files:")
    for f in md_files:
        print(f"  - {f.name}")
    
    # Process each file
    all_chunks = []
    for file_path in md_files:
        try:
            chunks = chunker.process_document(str(file_path))
            all_chunks.extend(chunks)
            print(f"  ✓ {file_path.name}: {len(chunks)} chunks")
        except Exception as e:
            print(f"  ✗ {file_path.name}: {e}")
    
    # Show statistics
    stats = chunker.get_statistics()
    print(f"\nDirectory Processing Statistics:")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Chunks with code: {stats['total_code_blocks']}")
    print(f"  - Average chunk size: {stats['average_chunk_size']:.1f} chars")
    print(f"  - Total processing time: {stats['processing_time_seconds']:.2f}s")
    print(f"  - Failed documents: {stats['failed_documents']}")


def demo_chunk_id_uniqueness():
    """Demo chunk ID uniqueness."""
    print("\n" + "=" * 80)
    print("Demo: Chunk ID Uniqueness")
    print("=" * 80)
    
    # Find sample documents
    sample_docs = list(Path("pipeline_output/downloaded_pages").glob("*.md"))[:2]
    
    if len(sample_docs) < 2:
        print("Need at least 2 documents for this demo. Skipping.")
        return
    
    print(f"\nProcessing 2 documents to verify chunk ID uniqueness:")
    for doc in sample_docs:
        print(f"  - {doc.name}")
    
    # Create orchestrator
    config = ChunkerConfig(generate_summaries=False, generate_embeddings=False)
    chunker = UserManualChunker.from_config(config)
    
    # Process documents
    all_chunk_ids = set()
    duplicate_ids = []
    
    for doc in sample_docs:
        try:
            chunks = chunker.process_document(str(doc))
            
            for chunk in chunks:
                if chunk.chunk_id in all_chunk_ids:
                    duplicate_ids.append(chunk.chunk_id)
                else:
                    all_chunk_ids.add(chunk.chunk_id)
        except Exception as e:
            print(f"  ✗ Error processing {doc.name}: {e}")
    
    print(f"\nResults:")
    print(f"  - Total chunks: {len(all_chunk_ids)}")
    print(f"  - Unique IDs: {len(all_chunk_ids)}")
    print(f"  - Duplicates: {len(duplicate_ids)}")
    
    if duplicate_ids:
        print(f"\n  ✗ Found duplicate IDs:")
        for dup_id in duplicate_ids:
            print(f"    - {dup_id}")
    else:
        print(f"\n  ✓ All chunk IDs are unique!")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("UserManualChunker Orchestrator Demo")
    print("=" * 80)
    
    # Demo 1: Single document processing
    chunks = demo_single_document()
    
    # Demo 2: JSON export
    if chunks:
        demo_json_export(chunks)
        demo_vector_db_export(chunks)
    
    # Demo 3: Directory processing
    demo_directory_processing()
    
    # Demo 4: Chunk ID uniqueness
    demo_chunk_id_uniqueness()
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
