#!/usr/bin/env python3
"""
Simple script to crawl URLs from a JSON file using basic crawling.
"""

import json
import sys
import os
import asyncio
from pathlib import Path

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import get_supabase_client, add_documents_to_supabase, create_embedding
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from urllib.parse import urlparse
import re

def load_urls_from_json(json_file: str) -> list:
    """Load URLs from a JSON file."""
    file_path = Path(json_file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        # Direct list of URLs: ["url1", "url2", ...]
        return data
    elif isinstance(data, dict) and 'urls' in data:
        # Object with urls key: {"urls": ["url1", "url2", ...]}
        return data['urls']
    else:
        raise ValueError("JSON must be a list of URLs or an object with 'urls' key")

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

async def crawl_single_url(crawler, supabase_client, url: str) -> bool:
    """Crawl a single URL and store in Supabase."""
    try:
        print(f"  Fetching content...")
        
        # Configure the crawl
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
        
        # Crawl the page
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success and result.markdown:
            print(f"  Got {len(result.markdown)} chars of content")
            
            # Extract source_id
            parsed_url = urlparse(url)
            source_id = parsed_url.netloc or parsed_url.path
            
            # Chunk the content
            chunks = smart_chunk_markdown(result.markdown)
            print(f"  Split into {len(chunks)} chunks")
            
            # Prepare data for Supabase
            urls = []
            chunk_numbers = []
            contents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                urls.append(url)
                chunk_numbers.append(i)
                contents.append(chunk)
                
                # Extract metadata
                meta = extract_section_info(chunk)
                meta["chunk_index"] = i
                meta["url"] = url
                meta["source"] = source_id
                metadatas.append(meta)
            
            # Create url_to_full_document mapping
            url_to_full_document = {url: result.markdown}
            
            print(f"  Storing in database...")
            
            # First, create/update the source record
            from src.utils import update_source_info, extract_source_summary
            total_word_count = sum(meta.get("word_count", 0) for meta in metadatas)
            source_summary = extract_source_summary(source_id, result.markdown[:5000])
            update_source_info(supabase_client, source_id, source_summary, total_word_count)
            
            # Then add documents to Supabase
            add_documents_to_supabase(supabase_client, urls, chunk_numbers, contents, metadatas, url_to_full_document)
            
            return True
        else:
            print(f"  Failed to get content: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
            return False
            
    except Exception as e:
        print(f"  Error: {e}")
        return False

async def crawl_urls(json_file: str):
    """Crawl all URLs from a JSON file."""
    try:
        print(f"Loading URLs from: {json_file}")
        urls = load_urls_from_json(json_file)
        
        print(f"Found {len(urls)} URLs to crawl")
        print()
        
        # Initialize crawler and Supabase
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.__aenter__()
        
        supabase_client = get_supabase_client()
        
        success_count = 0
        failed_count = 0
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] Crawling: {url}")
                
                success = await crawl_single_url(crawler, supabase_client, url)
                if success:
                    print(f"  ✅ Success")
                    success_count += 1
                else:
                    print(f"  ❌ Failed")
                    failed_count += 1
                
                print()
        finally:
            await crawler.__aexit__(None, None, None)
        
        # Summary
        print("=" * 50)
        print("CRAWLING COMPLETE")
        print(f"Total URLs: {len(urls)}")
        print(f"Successfully crawled: {success_count}")
        print(f"Failed: {failed_count}")
        if len(urls) > 0:
            print(f"Success rate: {success_count/len(urls)*100:.1f}%")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def create_example_json():
    """Create an example JSON file."""
    example_urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://docs.example.com/api"
    ]
    
    # Simple list format
    with open('urls_simple.json', 'w') as f:
        json.dump(example_urls, f, indent=2)
    
    print("Created example JSON file: urls_simple.json")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl URLs from a JSON file')
    parser.add_argument('json_file', nargs='?', help='JSON file containing URLs')
    parser.add_argument('--create-example', action='store_true', help='Create example JSON file')
    
    args = parser.parse_args()
    
    if args.create_example:
        create_example_json()
        return
    
    if not args.json_file:
        print("Error: Please provide a JSON file or use --create-example")
        print("Usage: python scripts/simple_crawl_json.py urls.json")
        print("       python scripts/simple_crawl_json.py --create-example")
        return
    
    asyncio.run(crawl_urls(args.json_file))

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()