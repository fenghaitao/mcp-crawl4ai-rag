#!/usr/bin/env python3
"""
Complete crawling pipeline: Extract URLs -> Download locally -> Clean DB -> Crawl local files
This script automates the entire process for clean, predictable crawling.
"""
import os
import sys
import json
import subprocess
import argparse
import asyncio
from pathlib import Path

def get_python_executable():
    """Get the appropriate Python executable (prefer .venv if available)."""
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
        print(f"🐍 Using virtual environment: {venv_python}")
        return str(venv_python)
    else:
        print(f"🐍 Using system Python: {sys.executable}")
        return sys.executable

def run_command(command: list, description: str) -> bool:
    """
    Run a command and handle errors.
    
    Args:
        command: Command to run as list
        description: Description for logging
        
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(command)}")
    print()
    
    try:
        result = subprocess.run(command, check=True, capture_output=False, text=True)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"📤 Output: {e.stdout}")
        if e.stderr:
            print(f"🚨 Error: {e.stderr}")
        return False
    except FileNotFoundError as e:
        print(f"\n💥 {description} failed: Script not found - {e}")
        return False
    except Exception as e:
        print(f"\n💥 {description} failed with error: {e}")
        return False

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and log the result."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath} exists")
        return True
    else:
        print(f"❌ {description}: {filepath} not found")
        return False

def main():
    """Main pipeline function."""
    parser = argparse.ArgumentParser(description='Complete crawling pipeline for local content')
    parser.add_argument('input_url', help='Initial URL to extract links from (e.g., sitemap or index page)')
    parser.add_argument('--output-dir', '-o', default='./pipeline_output', 
                       help='Directory for all pipeline outputs (default: ./pipeline_output)')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Skip database cleanup step')
    parser.add_argument('--skip-extraction', action='store_true',
                       help='Skip URL extraction (use existing URLs file)')
    parser.add_argument('--skip-download', action='store_true',
                       help='Skip page download (use existing local files)')
    parser.add_argument('--max-urls', type=int, default=None,
                       help='Maximum number of URLs to process')
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    extracted_urls_file = output_dir / "extracted_urls.json"
    downloaded_pages_dir = output_dir / "downloaded_pages"
    local_urls_file = output_dir / "local_urls.json"
    
    print(f"🚀 Starting Crawling Pipeline")
    print(f"Input URL: {args.input_url}")
    print(f"Output directory: {output_dir}")
    print(f"Skip cleanup: {args.skip_cleanup}")
    print(f"Skip extraction: {args.skip_extraction}")
    print(f"Skip download: {args.skip_download}")
    if args.max_urls:
        print(f"Max URLs to process: {args.max_urls}")
    
    # Get the correct Python executable
    python_exe = get_python_executable()
    
    # Step 1: Clean up database (optional)
    if not args.skip_cleanup:
        cleanup_success = run_command(
            [python_exe, "scripts/delete_all_records.py", "--confirm"],
            "Database Cleanup"
        )
        if not cleanup_success:
            print("⚠️  Database cleanup failed, but continuing...")
    else:
        print("\n🔄 Skipping database cleanup (--skip-cleanup)")
    
    # Step 2: Extract URLs from input URL
    if not args.skip_extraction:
        extract_command = [
            python_exe, "scripts/extract_simics_urls.py", 
            args.input_url, 
            "--output", str(extracted_urls_file)
        ]
        if args.max_urls:
            extract_command.extend(["--max-urls", str(args.max_urls)])
            
        extract_success = run_command(extract_command, "URL Extraction")
        if not extract_success:
            print("❌ URL extraction failed. Cannot continue.")
            return
        
        # Verify the output file was created
        if not check_file_exists(str(extracted_urls_file), "Extracted URLs file"):
            print("❌ URL extraction appeared to succeed but output file not found. Cannot continue.")
            return
    else:
        print(f"\n🔄 Skipping URL extraction (--skip-extraction)")
        if not check_file_exists(str(extracted_urls_file), "Existing URLs file"):
            print("❌ No existing URLs file found. Cannot continue without URL extraction.")
            return
    
    # Step 3: Download pages locally
    if not args.skip_download:
        download_success = run_command([
            python_exe, "scripts/download_pages_locally.py",
            str(extracted_urls_file),
            "--output-dir", str(downloaded_pages_dir),
            "--output-json", str(local_urls_file)
        ], "Local Page Download")
        if not download_success:
            print("❌ Page download failed. Cannot continue.")
            return
        
        # Verify the output file was created
        if not check_file_exists(str(local_urls_file), "Local URLs file"):
            print("❌ Page download appeared to succeed but output file not found. Cannot continue.")
            return
    else:
        print(f"\n🔄 Skipping page download (--skip-download)")
        if not check_file_exists(str(local_urls_file), "Existing local URLs file"):
            print("❌ No existing local URLs file found. Cannot continue without download.")
            return
    
    # Step 4: Crawl local files and update database
    crawl_success = run_command([
        python_exe, "scripts/crawl_local_files.py",
        str(downloaded_pages_dir)  # Pass the directory, not the JSON file
    ], "Local File Crawling")
    
    if not crawl_success:
        print("❌ Local file crawling failed. Cannot continue.")
        return
    
    # Step 5: Crawl Simics source code (if enabled)
    simics_enabled = os.getenv("CRAWL_SIMICS_SOURCE", "false").lower() == "true"
    if simics_enabled:
        simics_success = run_command([
            python_exe, "scripts/crawl_simics_source.py",
            "--output-dir", str(output_dir)
        ], "Simics Source Code Crawling")
        
        if not simics_success:
            print("⚠️  Simics source crawling failed, but continuing...")
    else:
        print("\n🔄 Skipping Simics source crawling (CRAWL_SIMICS_SOURCE=false)")
        simics_success = True  # Don't fail the pipeline if it's disabled
    
    # Final summary
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETE")
    print(f"{'='*60}")
    
    if crawl_success:
        print("✅ All steps completed successfully!")
        print("\nFiles created:")
        print(f"  📄 Extracted URLs: {extracted_urls_file}")
        print(f"  📁 Downloaded pages: {downloaded_pages_dir}")
        print(f"  📄 Local URLs: {local_urls_file}")
        print("\n🗄️  Database has been updated with local content")
        print("🔍 You can now perform RAG queries on the clean, local content")
    else:
        print("❌ Pipeline failed at the crawling step")
        print("🔍 Check the logs above for details")
    
    print(f"\n💡 To rerun parts of the pipeline:")
    print(f"   Skip cleanup: --skip-cleanup")
    print(f"   Skip extraction: --skip-extraction") 
    print(f"   Skip download: --skip-download")

if __name__ == "__main__":
    main()