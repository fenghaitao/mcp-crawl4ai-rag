#!/usr/bin/env python3
"""
Simple script to crawl URLs from a JSON file using crawl_single_page.
"""

import json
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the MCP crawl4ai tool function
from mcp__crawl4ai_rag__invoke_tool import mcp__crawl4ai_rag__invoke_tool

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

def crawl_urls(json_file: str):
    """Crawl all URLs from a JSON file."""
    try:
        print(f"Loading URLs from: {json_file}")
        urls = load_urls_from_json(json_file)
        
        print(f"Found {len(urls)} URLs to crawl")
        print()
        
        success_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Crawling: {url}")
            
            try:
                # Use the available MCP crawl4ai invoke tool function directly
                result = mcp__crawl4ai_rag__invoke_tool(
                    tool_name="crawl_single_page",
                    tool_input={"url": url}
                )
                
                # Parse the result to check if it was successful
                if result and "success" in str(result):
                    print(f"  ✅ Success")
                    success_count += 1
                else:
                    print(f"  ❌ Failed: {result}")
                    failed_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                failed_count += 1
            
            print()
        
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
        "https://docs.example.com/api",
        "https://docs.example.com/guide"
    ]
    
    # Create both formats as examples
    
    # Simple list format
    with open('urls_simple.json', 'w') as f:
        json.dump(example_urls, f, indent=2)
    
    # Object format
    example_object = {
        "urls": example_urls,
        "description": "Example URLs to crawl"
    }
    
    with open('urls_object.json', 'w') as f:
        json.dump(example_object, f, indent=2)
    
    print("Created example JSON files:")
    print("  - urls_simple.json (simple list format)")
    print("  - urls_object.json (object format)")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl URLs from a JSON file')
    parser.add_argument('json_file', nargs='?', help='JSON file containing URLs')
    parser.add_argument('--create-example', action='store_true', help='Create example JSON files')
    
    args = parser.parse_args()
    
    if args.create_example:
        create_example_json()
        return
    
    if not args.json_file:
        print("Error: Please provide a JSON file or use --create-example")
        print("Usage: python scripts/crawl_from_json.py urls.json")
        print("       python scripts/crawl_from_json.py --create-example")
        return
    
    crawl_urls(args.json_file)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()