#!/usr/bin/env python3
"""
Download a single HTML page without crawling external links.
Output is saved to pipeline_output/downloaded_pages for use with crawl_pipeline.py stages.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from urllib.parse import urlparse, urljoin
import json
import hashlib
from datetime import datetime

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


def sanitize_filename(url: str) -> str:
    """Create a safe filename from URL."""
    parsed = urlparse(url)
    
    # Create a descriptive name from the URL
    if parsed.path and parsed.path != '/':
        # Use the last part of the path
        path_parts = parsed.path.strip('/').split('/')
        name = path_parts[-1] if path_parts else 'index'
        # Remove file extension if present
        if '.' in name:
            name = name.rsplit('.', 1)[0]
    else:
        name = 'index'
    
    # Clean the name
    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).strip()
    if not safe_name:
        safe_name = 'page'
    
    # Add domain for uniqueness
    domain = parsed.netloc.replace('.', '_')
    
    # Create filename with hash to ensure uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    return f"{domain}_{safe_name}_{url_hash}"


def create_output_structure(output_dir: Path, url: str) -> dict:
    """Create the output directory structure and return paths."""
    
    # Create main directories
    downloaded_pages_dir = output_dir / "downloaded_pages"
    downloaded_pages_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = sanitize_filename(url)
    
    # Create paths
    paths = {
        'html_file': downloaded_pages_dir / f"{filename}.html"
    }
    
    return paths


async def download_single_page(url: str, output_dir: Path, user_agent: str = None) -> bool:
    """Download a single HTML page and save it in pipeline format."""
    
    print(f"🔗 Downloading: {url}")
    
    # Create output structure
    paths = create_output_structure(output_dir, url)
    
    # Configure crawler
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        user_agent=user_agent or "Mozilla/5.0 (compatible; SinglePageDownloader/1.0)"
    )
    
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.__aenter__()
    
    try:
        # Configure crawl settings
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            stream=False,
            word_count_threshold=10  # Minimum words to consider valid content
        )
        
        # Perform the crawl
        result = await crawler.arun(url=url, config=run_config)
        
        if not result.success:
            print(f"❌ Failed to download {url}: {result.error_message}")
            return False
        
        # Extract content information
        content_info = {
            'url': url,
            'title': result.metadata.get('title', '') if result.metadata else '',
            'description': result.metadata.get('description', '') if result.metadata else '',
            'downloaded_at': datetime.now().isoformat(),
            'status_code': getattr(result, 'status_code', 200),
            'content_type': '',  # headers not available in this version
            'word_count': len(result.cleaned_html.split()) if result.cleaned_html else 0,
            'char_count': len(result.cleaned_html) if result.cleaned_html else 0,
            'markdown_length': len(result.markdown) if result.markdown else 0
        }
        
        print(f"✅ Successfully downloaded: {content_info['title'] or 'Untitled'}")
        print(f"   📊 Content: {content_info['word_count']} words, {content_info['char_count']} chars")
        
        # Save HTML content only
        if result.html:
            with open(paths['html_file'], 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"   💾 Saved HTML: {paths['html_file']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False
        
    finally:
        await crawler.__aexit__(None, None, None)


def create_sitemap_file(output_dir: Path, url: str) -> bool:
    """Create a simple sitemap.txt file for pipeline compatibility."""
    
    sitemap_file = output_dir / "sitemap.txt"
    
    try:
        with open(sitemap_file, 'w', encoding='utf-8') as f:
            f.write(f"{url}\n")
        
        print(f"📄 Created sitemap: {sitemap_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sitemap: {e}")
        return False


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Download a single HTML page for pipeline processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a single page
  python scripts/download_single_page.py https://example.com/docs/page.html
  
  # Download with custom output directory
  python scripts/download_single_page.py https://example.com/docs/page.html --output-dir my_pipeline_output
  
  # Download with custom user agent
  python scripts/download_single_page.py https://example.com/docs/page.html --user-agent "MyBot/1.0"

Integration with pipeline:
  # After downloading, continue with pipeline stages
  python scripts/crawl_pipeline.py --skip-download --skip-extraction pipeline_output
        """
    )
    
    parser.add_argument('url', help='URL of the HTML page to download')
    parser.add_argument('--output-dir', type=str, default='pipeline_output',
                       help='Output directory (default: pipeline_output)')
    parser.add_argument('--user-agent', type=str,
                       help='Custom User-Agent string')
    parser.add_argument('--create-sitemap', action='store_true', default=True,
                       help='Create sitemap.txt for pipeline compatibility (default: true)')
    
    args = parser.parse_args()
    
    # Validate URL
    parsed_url = urlparse(args.url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print("❌ Error: Invalid URL provided")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Single Page Downloader")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🔗 Target URL: {args.url}")
    print()
    
    # Download the page
    success = await download_single_page(args.url, output_dir, args.user_agent)
    
    if not success:
        print("❌ Download failed")
        sys.exit(1)
    
    # Create sitemap for pipeline compatibility
    if args.create_sitemap:
        create_sitemap_file(output_dir, args.url)
    
    print()
    print("✅ Download completed successfully!")
    print()
    print("🔄 Next steps - Continue with pipeline stages:")
    print(f"   python scripts/crawl_pipeline.py --skip-download --skip-extraction {args.output_dir}")
    print()
    print("📁 Downloaded files:")
    downloaded_dir = output_dir / "downloaded_pages"
    if downloaded_dir.exists():
        for file in sorted(downloaded_dir.glob("*")):
            print(f"   {file.name}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the main function
    asyncio.run(main())