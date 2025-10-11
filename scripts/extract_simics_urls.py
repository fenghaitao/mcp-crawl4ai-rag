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

async def extract_simics_urls():
    """Extract all URLs from the Simics DML reference manual index."""
    
    index_url = "https://intel.github.io/simics/docs/dml-1.4-reference-manual/index.html"
    base_url = "https://intel.github.io/simics/docs/dml-1.4-reference-manual/"
    
    print(f"Crawling Simics index page: {index_url}")
    
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
            
            # Only include URLs from the same documentation set
            if 'dml-1.4-reference-manual' in url and url.endswith('.html'):
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

def save_urls_to_json(urls, filename="simics_dml_urls.json"):
    """Save URLs to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(urls, f, indent=2)
    
    print(f"\n✅ Saved {len(urls)} URLs to {filename}")
    print(f"📝 You can now crawl all URLs with:")
    print(f"   .venv/bin/python scripts/simple_crawl_json.py {filename}")

async def main():
    """Main function."""
    try:
        urls = await extract_simics_urls()
        
        if urls:
            save_urls_to_json(urls)
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
