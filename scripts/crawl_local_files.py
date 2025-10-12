#!/usr/bin/env python3
"""
Crawl local HTML files by reading them directly and processing with Crawl4AI's raw content feature.
This bypasses the file:// URL handling bug in Crawl4AI.
"""
import os
import json
import sys
import asyncio
from pathlib import Path
from urllib.parse import urlparse
import re
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import (
    get_supabase_client, add_documents_to_supabase, update_source_info, extract_source_summary,
    extract_code_blocks, generate_code_example_summary, add_code_examples_to_supabase
)
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

def smart_chunk_markdown(text: str, chunk_size: int = 5000) -> list:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = end

    return chunks

def extract_section_info(chunk: str) -> dict:
    """Extract headers and stats from a chunk."""
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }

def get_original_url_from_filename(filename: str) -> str:
    """Extract original URL from downloaded filename."""
    # Remove file extension
    base = filename.replace('.html', '')
    
    # Split by underscores and reconstruct URL
    if 'simics_docs_dml-1.4-reference-manual_' in base:
        page_name = base.replace('simics_docs_dml-1.4-reference-manual_', '')
        return f"https://intel.github.io/simics/docs/dml-1.4-reference-manual/{page_name}.html"
    
    # Fallback: return the filename as-is
    return f"local://{filename}"

async def crawl_local_file(crawler, supabase_client, file_path: str, delete_existing: bool = True) -> bool:
    """Crawl a single local HTML file."""
    try:
        logging.info(f"  Reading file: {file_path}")
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logging.info(f"  File size: {len(html_content)} characters")
        
        # Get the original URL for metadata
        filename = Path(file_path).name
        original_url = get_original_url_from_filename(filename)
        
        # Use Crawl4AI's raw content processing
        raw_url = f"raw:{html_content}"
        
        # Configure the crawl with simple, reliable configuration
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS, 
            stream=False,
            page_timeout=3000,  # 3 seconds timeout for reliability
            delay_before_return_html=0  # No delay for faster crawling
        )
        
        # Process the HTML with Crawl4AI
        result = await crawler.arun(url=raw_url, config=run_config)
        
        if result.success and result.markdown:
            logging.info(f"  ✅ Processed successfully")
            logging.info(f"  📄 Markdown content: {len(result.markdown)} characters")
            
            # Extract source_id from original URL
            parsed_url = urlparse(original_url)
            source_id = parsed_url.netloc or parsed_url.path
            
            # Chunk the content
            chunks = smart_chunk_markdown(result.markdown)
            logging.info(f"  📦 Split into {len(chunks)} chunks")
            
            # Prepare data for Supabase
            urls = []
            chunk_numbers = []
            contents = []
            metadatas = []
            total_word_count = 0
            
            for i, chunk in enumerate(chunks):
                urls.append(original_url)  # Use original URL, not file path
                chunk_numbers.append(i)
                contents.append(chunk)
                
                # Extract metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = i
                meta["url"] = original_url
                meta["source"] = source_id
                meta["local_file"] = file_path  # Keep track of local file
                metadatas.append(meta)
                
                # Accumulate word count
                total_word_count += meta.get("word_count", 0)
            
            # Create url_to_full_document mapping
            url_to_full_document = {original_url: result.markdown}
            
            logging.info(f"  💾 Storing in database...")
            
            # First, create/update the source record
            source_summary = extract_source_summary(source_id, result.markdown[:5000])
            update_source_info(supabase_client, source_id, source_summary, total_word_count)
            
            # Ensure all metadata contains the correct source_id
            for meta in metadatas:
                meta["source_id"] = source_id
            
            # Then add documents to Supabase
            add_documents_to_supabase(supabase_client, urls, chunk_numbers, contents, metadatas, url_to_full_document, delete_existing)
            
            # Extract and process code examples if enabled
            agentic_rag_enabled = os.getenv("USE_AGENTIC_RAG", "false").lower() == "true"
            if agentic_rag_enabled:
                logging.info(f"  🔬 Extracting code examples...")
                code_blocks = extract_code_blocks(result.markdown)
                
                if code_blocks:
                    logging.info(f"  📝 Found {len(code_blocks)} code blocks, generating summaries...")
                    
                    # Generate summaries for code examples in parallel
                    def process_code_example(args):
                        code, context_before, context_after = args
                        return generate_code_example_summary(code, context_before, context_after)
                    
                    summary_args = [
                        (block['code'], block['context_before'], block['context_after'])
                        for block in code_blocks
                    ]
                    
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        summaries = list(executor.map(process_code_example, summary_args))
                    
                    # Prepare code example data
                    code_urls = []
                    code_chunk_numbers = []
                    code_examples = []
                    code_summaries = []
                    code_metadatas = []
                    
                    for i, (block, summary) in enumerate(zip(code_blocks, summaries)):
                        code_urls.append(original_url)
                        code_chunk_numbers.append(i)
                        code_examples.append(block['code'])
                        code_summaries.append(summary)
                        
                        # Create metadata for code example
                        code_meta = {
                            "chunk_index": i,
                            "url": original_url,
                            "source": source_id,
                            "source_id": source_id,
                            "local_file": file_path,
                            "code_length": len(block['code']),
                            "language": block.get('language', 'unknown')
                        }
                        code_metadatas.append(code_meta)
                    
                    # Add code examples to Supabase
                    add_code_examples_to_supabase(
                        supabase_client,
                        code_urls,
                        code_chunk_numbers,
                        code_examples,
                        code_summaries,
                        code_metadatas,
                        delete_existing
                    )
                    
                    logging.info(f"  ✅ Stored {len(code_blocks)} code examples")
                else:
                    logging.info(f"  📝 No code blocks found")
            else:
                logging.info(f"  🔬 Code example extraction disabled (USE_AGENTIC_RAG=false)")
            
            return True
        else:
            logging.error(f"  ❌ Failed to process: {getattr(result, 'error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        logging.error(f"  💥 Error: {e}")
        return False

async def crawl_local_files(directory: str, delete_existing: bool = True):
    """Crawl all HTML files in a directory."""
    directory_path = Path(directory)
    
    if not directory_path.exists():
        logging.error(f"❌ Directory not found: {directory}")
        return
    
    # Find all HTML files
    html_files = list(directory_path.glob("*.html"))
    
    if not html_files:
        logging.error(f"❌ No HTML files found in: {directory}")
        return
    
    logging.info(f"📁 Found {len(html_files)} HTML files in {directory}")
    logging.info("🔄 Processing with Crawl4AI raw content...")
    logging.info("")
    
    # Initialize crawler and Supabase
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    supabase_client = get_supabase_client()
    
    success_count = 0
    failed_count = 0
    
    try:
        for i, file_path in enumerate(html_files, 1):
            logging.info(f"[{i}/{len(html_files)}] Processing: {file_path.name}")
            
            success = await crawl_local_file(crawler, supabase_client, str(file_path), delete_existing)
            
            if success:
                success_count += 1
                logging.info("  ✅ Success")
            else:
                failed_count += 1
                logging.error("  ❌ Failed")
            logging.info("")
        
    finally:
        await crawler.__aexit__(None, None, None)
    
    # Summary
    logging.info("=" * 60)
    logging.info("LOCAL CRAWLING COMPLETE")
    logging.info(f"Total files: {len(html_files)}")
    logging.info(f"Successfully processed: {success_count}")
    logging.info(f"Failed: {failed_count}")
    logging.info(f"Success rate: {success_count/len(html_files)*100:.1f}%")
    
    if success_count > 0:
        logging.info("\n🎉 Files have been processed and stored in your Supabase database!")
        logging.info("You can now search and query the content using your RAG system.")

def setup_logging(log_file=None):
    """Setup logging configuration."""
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(message)s')
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (always present, shows simple format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified, shows detailed format)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        print(f"📄 Logging detailed output to: {log_file}")
    
    return logger

def log_print(message, level=logging.INFO):
    """Print message and log it."""
    # For console, just print normally
    print(message)
    # For file, log with timestamp
    logging.log(level, message)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Crawl local HTML files and process with Crawl4AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawl_local_files.py pipeline_output/downloaded_pages/
  python crawl_local_files.py pipeline_output/downloaded_pages/ --log-file crawl_output.log
  python crawl_local_files.py pipeline_output/downloaded_pages/ --log-file logs/crawl_$(date +%Y%m%d_%H%M%S).log
        """
    )
    
    parser.add_argument(
        'directory',
        help='Directory containing HTML files to crawl'
    )
    
    parser.add_argument(
        '--log-file', '-l',
        help='Optional log file to save detailed output (with timestamps)'
    )
    
    parser.add_argument(
        '--skip-delete', 
        action='store_true',
        default=True,
        help='Skip deleting existing records before inserting (default: True for faster incremental updates)'
    )
    
    parser.add_argument(
        '--force-delete',
        action='store_true', 
        help='Force deletion of existing records before inserting (overrides --skip-delete)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_file)
    
    # Determine delete behavior
    delete_existing = args.force_delete or not args.skip_delete
    
    # Log run information
    if args.log_file:
        # Show the full command line that was executed
        import shlex
        full_command = "python " + " ".join(shlex.quote(arg) for arg in sys.argv)
        logger.info(f"Command: {full_command}")
        logger.info(f"Started: {datetime.now().isoformat()}")
        logger.info(f"Directory: {args.directory}")
        logger.info(f"Log file: {args.log_file}")
        logger.info(f"Delete existing records: {delete_existing}")
        logger.info("-" * 80)
    
    asyncio.run(crawl_local_files(args.directory, delete_existing))

if __name__ == "__main__":
    main()