#!/usr/bin/env python3
"""
User Manual Chunking Script.

Processes user manual documents (markdown/HTML) and generates chunks with
embeddings and metadata for RAG retrieval. Optionally uploads to Supabase.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from user_manual_chunker import UserManualChunker
from user_manual_chunker.config import ChunkerConfig
from utils import get_supabase_client, add_documentation_chunks_to_supabase


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main function for user manual chunking."""
    parser = argparse.ArgumentParser(
        description='Process user manual documents for RAG'
    )
    parser.add_argument(
        'input_path',
        help='Path to input file or directory'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='./manual_chunks',
        help='Output directory for chunks (default: ./manual_chunks)'
    )
    parser.add_argument(
        '--pattern',
        default='*.md',
        help='File pattern for directory processing (default: *.md)'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Disable recursive directory search'
    )
    parser.add_argument(
        '--no-embeddings',
        action='store_true',
        help='Skip embedding generation'
    )
    parser.add_argument(
        '--no-summaries',
        action='store_true',
        help='Skip summary generation'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse and chunk without generating embeddings or summaries'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--upload-to-supabase',
        action='store_true',
        help='Upload chunks to Supabase database'
    )
    parser.add_argument(
        '--skip-delete',
        action='store_true',
        help='Skip deleting existing records (use upsert instead)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for Supabase uploads (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate input path
    input_path = Path(args.input_path)
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("User Manual Chunking")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Load configuration from environment
    config = ChunkerConfig.from_env()
    
    # Override config based on arguments
    if args.dry_run or args.no_embeddings:
        config.generate_embeddings = False
    if args.dry_run or args.no_summaries:
        config.generate_summaries = False
    
    logger.info(f"Configuration:")
    logger.info(f"  Max chunk size: {config.max_chunk_size}")
    logger.info(f"  Min chunk size: {config.min_chunk_size}")
    logger.info(f"  Chunk overlap: {config.chunk_overlap}")
    logger.info(f"  Generate embeddings: {config.generate_embeddings}")
    logger.info(f"  Generate summaries: {config.generate_summaries}")
    
    # Create chunker
    try:
        chunker = UserManualChunker.from_config(config)
    except Exception as e:
        logger.error(f"Failed to initialize chunker: {e}")
        sys.exit(1)
    
    # Process input
    try:
        if input_path.is_file():
            logger.info(f"Processing single file: {input_path}")
            chunks = chunker.process_document(
                str(input_path),
                generate_embeddings=config.generate_embeddings,
                generate_summaries=config.generate_summaries
            )
        else:
            logger.info(f"Processing directory: {input_path}")
            logger.info(f"Pattern: {args.pattern}")
            logger.info(f"Recursive: {not args.no_recursive}")
            
            chunks = chunker.process_directory(
                str(input_path),
                pattern=args.pattern,
                recursive=not args.no_recursive
            )
        
        logger.info(f"Processed {len(chunks)} chunks")
        
        # Export results
        if chunks:
            # Export to standard JSON format
            json_output = output_dir / "chunks.json"
            logger.info(f"Exporting to {json_output}")
            chunker.export_to_json(chunks, str(json_output))
            
            # Export to vector DB format
            vector_db_output = output_dir / "vector_db_chunks.json"
            logger.info(f"Exporting to vector DB format: {vector_db_output}")
            chunker.export_to_vector_db_format(chunks, str(vector_db_output))
            
            # Upload to Supabase if requested
            if args.upload_to_supabase:
                logger.info("=" * 60)
                logger.info("Uploading to Supabase")
                logger.info("=" * 60)
                
                try:
                    # Get Supabase client
                    supabase_client = get_supabase_client()
                    logger.info("✓ Connected to Supabase")
                    
                    # Convert ProcessedChunk objects to dictionaries
                    chunk_dicts = [chunk.to_dict() for chunk in chunks]
                    
                    # Upload to Supabase
                    logger.info(f"Uploading {len(chunk_dicts)} chunks...")
                    logger.info(f"Delete existing: {not args.skip_delete}")
                    logger.info(f"Batch size: {args.batch_size}")
                    
                    add_documentation_chunks_to_supabase(
                        client=supabase_client,
                        chunks=chunk_dicts,
                        delete_existing=not args.skip_delete,
                        batch_size=args.batch_size
                    )
                    
                    logger.info("✓ Upload to Supabase complete!")
                    
                except Exception as e:
                    logger.error(f"Failed to upload to Supabase: {e}", exc_info=True)
                    logger.warning("Chunks were saved to local files but not uploaded to database")
            
            # Print statistics
            stats = chunker.get_statistics()
            logger.info("=" * 60)
            logger.info("Processing Statistics")
            logger.info("=" * 60)
            logger.info(f"Total documents: {stats['total_documents']}")
            logger.info(f"Total chunks: {stats['total_chunks']}")
            logger.info(f"Total code blocks: {stats['total_code_blocks']}")
            logger.info(f"Average chunk size: {stats['average_chunk_size']:.1f} chars")
            logger.info(f"Processing time: {stats['processing_time_seconds']:.2f}s")
            logger.info(f"Failed documents: {stats['failed_documents']}")
            
            logger.info("=" * 60)
            logger.info("✅ User manual chunking complete!")
            logger.info("=" * 60)
        else:
            logger.warning("No chunks were generated")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
