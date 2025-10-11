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

async def crawl_local_file(crawler, supabase_client, file_path: str) -> bool:
    """Crawl a single local HTML file."""
    try:
        print(f"  Reading file: {file_path}")
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"  File size: {len(html_content)} characters")
        
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
            print(f"  ✅ Processed successfully")
            print(f"  📄 Markdown content: {len(result.markdown)} characters")
            
            # Extract source_id from original URL
            parsed_url = urlparse(original_url)
            source_id = parsed_url.netloc or parsed_url.path
            
            # Chunk the content
            chunks = smart_chunk_markdown(result.markdown)
            print(f"  📦 Split into {len(chunks)} chunks")
            
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
            
            print(f"  💾 Storing in database...")
            
            # First, create/update the source record
            source_summary = extract_source_summary(source_id, result.markdown[:5000])
            update_source_info(supabase_client, source_id, source_summary, total_word_count)
            
            # Then add documents to Supabase
            add_documents_to_supabase(supabase_client, urls, chunk_numbers, contents, metadatas, url_to_full_document)
            
            # Extract and process code examples if enabled
            agentic_rag_enabled = os.getenv("USE_AGENTIC_RAG", "false").lower() == "true"
            if agentic_rag_enabled:
                print(f"  🔬 Extracting code examples...")
                code_blocks = extract_code_blocks(result.markdown)
                
                if code_blocks:
                    print(f"  📝 Found {len(code_blocks)} code blocks, generating summaries...")
                    
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
                        code_metadatas
                    )
                    
                    print(f"  ✅ Stored {len(code_blocks)} code examples")
                else:
                    print(f"  📝 No code blocks found")
            else:
                print(f"  🔬 Code example extraction disabled (USE_AGENTIC_RAG=false)")
            
            return True
        else:
            print(f"  ❌ Failed to process: {getattr(result, 'error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  💥 Error: {e}")
        return False

async def crawl_local_files(directory: str):
    """Crawl all HTML files in a directory."""
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    # Find all HTML files
    html_files = list(directory_path.glob("*.html"))
    
    if not html_files:
        print(f"❌ No HTML files found in: {directory}")
        return
    
    print(f"📁 Found {len(html_files)} HTML files in {directory}")
    print("🔄 Processing with Crawl4AI raw content...")
    print()
    
    # Initialize crawler and Supabase
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    supabase_client = get_supabase_client()
    
    success_count = 0
    failed_count = 0
    
    try:
        for i, file_path in enumerate(html_files, 1):
            print(f"[{i}/{len(html_files)}] Processing: {file_path.name}")
            
            success = await crawl_local_file(crawler, supabase_client, str(file_path))
            
            if success:
                success_count += 1
                print("  ✅ Success")
            else:
                failed_count += 1
                print("  ❌ Failed")
            print()
        
    finally:
        await crawler.__aexit__(None, None, None)
    
    # Summary
    print("=" * 60)
    print("LOCAL CRAWLING COMPLETE")
    print(f"Total files: {len(html_files)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {success_count/len(html_files)*100:.1f}%")
    
    if success_count > 0:
        print("\n🎉 Files have been processed and stored in your Supabase database!")
        print("You can now search and query the content using your RAG system.")

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python crawl_local_files.py <directory>")
        print("Example: python crawl_local_files.py downloaded_simics_pages")
        sys.exit(1)
    
    directory = sys.argv[1]
    asyncio.run(crawl_local_files(directory))

if __name__ == "__main__":
    main()