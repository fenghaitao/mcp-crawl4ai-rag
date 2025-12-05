#!/usr/bin/env python3
"""
Extract all documentation URLs from the Simics DML reference manual index page.
"""

import asyncio
import json
import sys
import os
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def extract_simics_urls(index_url: str):
    """Extract all URLs from the given index page."""
    
    # Determine base URL from the input URL
    parsed_url = urlparse(index_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
    
    print(f"Crawling index page: {index_url}")
    print(f"Base URL: {base_url}")
    
    # Initialize crawler
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    try:
        # Crawl the index page
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)
        result = await crawler.arun(url=index_url, config=run_config)
        
        if not result.success:
            print(f"Failed to crawl index page: {result.error_message}")
            return []
        
        print(f"Successfully crawled index page ({len(result.html)} chars)")
        
        # Extract all links from the HTML
        html_content = result.html
        
        # Find all href attributes pointing to .html files
        link_pattern = r'href="([^"]*\.html[^"]*)"'
        matches = re.findall(link_pattern, html_content)
        
        # Process and filter URLs
        documentation_urls = set()
        
        for match in matches:
            # Clean up the URL
            url = match.strip()
            
            # Skip fragments-only links
            if url.startswith('#'):
                continue
            
            # Convert relative URLs to absolute
            if url.startswith('./') or not url.startswith('http'):
                url = urljoin(base_url, url.lstrip('./'))
            
            # Only include URLs from the same base domain/path and ending in .html
            if url.startswith(base_url) and url.endswith('.html'):
                # Remove fragment identifiers for the main URL list
                clean_url = url.split('#')[0]
                documentation_urls.add(clean_url)
        
        # Convert to sorted list
        url_list = sorted(list(documentation_urls))
        
        print(f"\nFound {len(url_list)} unique documentation URLs:")
        for i, url in enumerate(url_list, 1):
            filename = url.split('/')[-1]
            print(f"  {i:2d}. {filename}")
        
        return url_list
        
    finally:
        await crawler.__aexit__(None, None, None)

def save_urls_to_json(urls, filename="extracted_urls.json"):
    """Save URLs to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(urls, f, indent=2)
    
    print(f"\n✅ Saved {len(urls)} URLs to {filename}")
    print(f"📝 You can now crawl all URLs with:")
    print(f"   .venv/bin/python scripts/crawl_local_files.py {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract URLs from a documentation site')
    parser.add_argument('input_url', help='URL to extract links from (index page, sitemap, etc.)')
    parser.add_argument('--output', '-o', default='extracted_urls.json', 
                       help='Output JSON file (default: extracted_urls.json)')
    parser.add_argument('--max-urls', type=int, default=None,
                       help='Maximum number of URLs to extract')
    
    args = parser.parse_args()
    
    try:
        urls = await extract_simics_urls(args.input_url)
        
        if args.max_urls and len(urls) > args.max_urls:
            print(f"🔢 Limiting to {args.max_urls} URLs (found {len(urls)})")
            urls = urls[:args.max_urls]
        
        if urls:
            save_urls_to_json(urls, args.output)
        else:
            print("❌ No URLs found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
