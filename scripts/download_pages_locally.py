#!/usr/bin/env python3
"""
Download web pages locally and create a JSON file with file:// URLs for crawling.
This allows us to crawl static content without any server-side processing.
"""
import os
import json
import requests
import argparse
from urllib.parse import urlparse, urljoin
from pathlib import Path

def download_page(url: str, output_dir: Path) -> str:
    """
    Download a single page and save it locally.
    
    Args:
        url: URL to download
        output_dir: Directory to save the file
        
    Returns:
        Local file path
    """
    try:
        print(f"📥 Downloading: {url}")
        
        # Get the page content
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create filename from URL
        parsed = urlparse(url)
        filename = parsed.path.replace('/', '_').replace('\\', '_')
        if not filename or filename == '_':
            filename = parsed.netloc.replace('.', '_')
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Clean up filename
        filename = filename.strip('_')
        if filename.startswith('_'):
            filename = filename[1:]
            
        filepath = output_dir / filename
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"   ✅ Saved: {filepath} ({len(response.text)} chars)")
        return str(filepath.absolute())
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None

def create_file_urls_json(local_files: list, output_file: str):
    """Create a JSON file with file:// URLs."""
    file_urls = []
    
    for filepath in local_files:
        if filepath:
            # Convert to file:// URL
            file_url = f"file://{filepath}"
            file_urls.append(file_url)
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(file_urls, f, indent=2)
    
    print(f"\n📄 Created {output_file} with {len(file_urls)} file:// URLs")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Download web pages locally for crawling')
    parser.add_argument('input_json', help='JSON file containing URLs to download')
    parser.add_argument('--output-dir', '-o', default='./downloaded_pages', 
                       help='Directory to save downloaded pages (default: ./downloaded_pages)')
    parser.add_argument('--output-json', '-j', default='./local_urls.json',
                       help='Output JSON file with file:// URLs (default: ./local_urls.json)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"🌐 Downloading pages to: {output_dir}")
    print(f"📄 Will create JSON file: {args.output_json}")
    print()
    
    # Load URLs to download
    try:
        with open(args.input_json, 'r') as f:
            urls = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {args.input_json}: {e}")
        return
    
    print(f"📋 Found {len(urls)} URLs to download")
    print()
    
    # Download each page
    local_files = []
    success_count = 0
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Processing: {url}")
        local_file = download_page(url, output_dir)
        local_files.append(local_file)
        
        if local_file:
            success_count += 1
        print()
    
    # Create file URLs JSON
    create_file_urls_json(local_files, args.output_json)
    
    # Summary
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print(f"Successfully downloaded: {success_count}/{len(urls)} pages")
    print(f"Local files saved in: {output_dir}")
    print(f"File URLs JSON: {args.output_json}")
    print()
    print("Next steps:")
    venv_python = ".venv/bin/python" if os.path.exists(".venv/bin/python") else "python"
    print(f"1. {venv_python} scripts/crawl_local_files.py {args.output_json}")
    print(f"2. Compare content sizes with original web crawling")

if __name__ == "__main__":
    main()
