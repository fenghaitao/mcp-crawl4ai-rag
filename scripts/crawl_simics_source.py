#!/usr/bin/env python3
"""
Crawl Simics Source Code - DML and Python files from the Simics packages.
This script processes DML and Python files from the Simics submodule and adds them to the RAG database.
"""
import os
import sys
import json
import asyncio
import re
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def get_github_commit_hash(simics_base_path: str) -> str:
    """Get the current GitHub commit hash for the simics repository."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=simics_base_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        logging.warning(f"Failed to get git commit hash: {e}")
        # Fallback to known commit
        return "f1b35684a083ae1f33e5f625ba18d2bd50f75f3c"

def get_github_url_for_file(file_path: str, simics_base_path: str) -> str:
    """Convert a local file path to a GitHub URL."""
    try:
        # GitHub repository information
        github_repo_url = "https://github.com/fenghaitao/simics-7-packages-2025-38-linux64"
        github_commit = get_github_commit_hash(simics_base_path)
        
        # Convert absolute path to relative path within the simics directory
        file_path = os.path.abspath(file_path)
        simics_base_path = os.path.abspath(simics_base_path)
        
        # Get the relative path from the simics base directory
        if file_path.startswith(simics_base_path):
            relative_path = os.path.relpath(file_path, simics_base_path)
            # Convert Windows-style path separators to forward slashes for URL
            relative_path = relative_path.replace(os.sep, '/')
            
            # Construct GitHub blob URL
            github_url = f"{github_repo_url}/blob/{github_commit}/{relative_path}"
            return github_url
        else:
            # Fallback to file:// URL if path is outside simics directory
            return f"file://{file_path}"
            
    except Exception as e:
        logging.warning(f"Failed to generate GitHub URL for {file_path}: {e}")
        return f"file://{os.path.abspath(file_path)}"

def find_simics_source_files(simics_path: str) -> Dict[str, List[str]]:
    """Find DML and Python files in Simics packages."""
    simics_path = Path(simics_path)
    
    if not simics_path.exists():
        logging.error(f"❌ Simics path not found: {simics_path}")
        return {'dml': [], 'python': []}
    
    logging.info(f"🔍 Searching for source files in: {simics_path}")
    start_time = time.time()
    
    # Find DML files
    logging.info("   📄 Scanning for DML files...")
    dml_files = list(simics_path.rglob("*.dml"))
    logging.info(f"   ✅ Found {len(dml_files)} DML files")
    
    # Find Python files
    logging.info("   🐍 Scanning for Python files...")
    python_files = list(simics_path.rglob("*.py"))
    logging.info(f"   ✅ Found {len(python_files)} Python files")
    
    elapsed = time.time() - start_time
    total_files = len(dml_files) + len(python_files)
    logging.info(f"   🕒 File discovery completed in {elapsed:.1f}s ({total_files} total files)")
    
    return {
        'dml': [str(f) for f in dml_files],
        'python': [str(f) for f in python_files]
    }

def extract_dml_metadata(content: str, file_path: str) -> dict:
    """Extract DML-specific metadata."""
    metadata = {
        'file_path': file_path,
        'file_type': 'dml',
        'language': 'dml'
    }
    
    # Extract device name
    device_match = re.search(r'device\s+(\w+)', content)
    if device_match:
        metadata['device_name'] = device_match.group(1)
    
    # Extract templates (is template_name)
    template_matches = re.findall(r'is\s+(\w+)', content)
    if template_matches:
        metadata['templates'] = list(set(template_matches))
    
    # Extract interfaces (implement interface_name)
    interface_matches = re.findall(r'implement\s+(\w+)', content)
    if interface_matches:
        metadata['interfaces'] = list(set(interface_matches))
    
    # Extract register groups
    register_matches = re.findall(r'group\s+(\w+)', content)
    if register_matches:
        metadata['register_groups'] = list(set(register_matches))
    
    # Extract methods
    method_matches = re.findall(r'method\s+(\w+)', content)
    if method_matches:
        metadata['methods'] = list(set(method_matches))
    
    # Calculate basic stats
    metadata['line_count'] = len(content.split('\n'))
    metadata['char_count'] = len(content)
    
    return metadata

def extract_python_metadata(content: str, file_path: str) -> dict:
    """Extract Python-specific metadata."""
    metadata = {
        'file_path': file_path,
        'file_type': 'python',
        'language': 'python'
    }
    
    # Extract class definitions
    class_matches = re.findall(r'class\s+(\w+)', content)
    if class_matches:
        metadata['classes'] = list(set(class_matches))
    
    # Extract function definitions
    function_matches = re.findall(r'def\s+(\w+)', content)
    if function_matches:
        metadata['functions'] = list(set(function_matches))
    
    # Extract Simics imports
    simics_imports = re.findall(r'import\s+(simics\S*)', content)
    simics_from_imports = re.findall(r'from\s+(simics\S*)', content)
    all_simics_imports = simics_imports + simics_from_imports
    if all_simics_imports:
        metadata['simics_imports'] = list(set(all_simics_imports))
    
    # Check if it's a device Python file
    if 'simics' in content and ('device' in content.lower() or 'component' in content.lower()):
        metadata['is_device_implementation'] = True
    else:
        metadata['is_device_implementation'] = False
    
    # Calculate basic stats
    metadata['line_count'] = len(content.split('\n'))
    metadata['char_count'] = len(content)
    
    return metadata

def determine_source_id(file_type: str) -> str:
    """Determine source_id based on file type."""
    if file_type == 'dml':
        return "simics-dml"
    elif file_type == 'python':
        return "simics-python"
    else:
        return "simics-source"

def process_source_file(file_path: str, file_index: int = 0, total_files: int = 0) -> Dict[str, Any]:
    """Process a single source file."""
    try:
        progress_info = f"[{file_index}/{total_files}]" if total_files > 0 else ""
        logging.info(f"  📄 {progress_info} Processing: {Path(file_path).name}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Determine file type
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.dml':
            file_type = 'dml'
            metadata = extract_dml_metadata(content, file_path)
        elif file_ext == '.py':
            file_type = 'python'
            metadata = extract_python_metadata(content, file_path)
        else:
            logging.warning(f"    ⚠️  Unknown file type: {file_ext}")
            return None
        
        # Determine source ID
        source_id = determine_source_id(file_type)
        
        logging.info(f"    ✅ {file_type.upper()} file, {len(content)} chars, source_id: {source_id}")
        
        return {
            'file_path': file_path,
            'content': content,
            'file_type': file_type,
            'source_id': source_id,
            'metadata': metadata
        }
        
    except Exception as e:
        logging.error(f"    ❌ Error processing {file_path}: {e}")
        return None

async def add_source_files_to_supabase(processed_files: List[Dict[str, Any]], simics_base_path: str, delete_existing: bool = True):
    """Add processed source files to Supabase."""
    try:
        from utils import get_supabase_client, add_documents_to_supabase
        from utils import update_source_info, extract_source_summary
        
        # Import smart_chunk_source from crawl4ai_mcp
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from crawl4ai_mcp import smart_chunk_source
        from urllib.parse import urlparse
        
        client = get_supabase_client()
        agentic_rag_enabled = os.getenv("USE_AGENTIC_RAG", "false").lower() == "true"
        
        logging.info(f"\n💾 Adding {len(processed_files)} source files to Supabase...")
        logging.info(f"🔬 Agentic RAG (code examples): {'Enabled' if agentic_rag_enabled else 'Disabled'}")
        
        # Group files by source_id for batch processing
        files_by_source = {}
        for file_data in processed_files:
            source_id = file_data['source_id']
            if source_id not in files_by_source:
                files_by_source[source_id] = []
            files_by_source[source_id].append(file_data)
        
        # Process each source type
        source_count = 0
        total_sources = len(files_by_source)
        for source_id, files in files_by_source.items():
            source_count += 1
            logging.info(f"\n📁 [{source_count}/{total_sources}] Processing {len(files)} files for source: {source_id}")
            
            # Prepare data for batch insertion
            urls = []
            chunk_numbers = []
            contents = []
            metadatas = []
            url_to_full_document = {}
            
            # Note: Code example extraction is skipped for source code files
            # The AST-aware chunks already provide well-structured code segments
            
            file_batch_count = 0
            for file_data in files:
                file_batch_count += 1
                file_path = file_data['file_path']
                content = file_data['content']
                metadata = file_data['metadata']
                
                # Create GitHub URL for the source file
                file_url = get_github_url_for_file(file_path, simics_base_path)
                
                # Determine source type from file extension
                source_type = metadata['language']
                
                # Chunk the content using AST-aware chunking
                chunk_dicts = smart_chunk_source(
                    code=content,
                    source_type=source_type,
                    max_chunk_size=2000,  # Smaller chunks for source code
                    chunk_overlap=20,  # Small overlap for context
                    file_path=file_path
                )
                logging.info(f"  📦 [{file_batch_count}/{len(files)}] {Path(file_path).name}: {len(chunk_dicts)} {source_type.upper()} chunks")
                
                # Add chunks for document storage
                for i, chunk_dict in enumerate(chunk_dicts):
                    urls.append(file_url)
                    chunk_numbers.append(i)
                    contents.append(chunk_dict["content"])
                    
                    # Enhance metadata with chunk info and AST metadata
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": i,
                        "url": file_url,
                        "source_id": source_id,
                        "crawl_time": "simics_source_crawl",
                        "source_type": source_type,
                        "chunking_method": "ast_aware"
                    })
                    # Merge AST metadata if available
                    if chunk_dict.get("metadata"):
                        chunk_metadata.update(chunk_dict["metadata"])
                    metadatas.append(chunk_metadata)
                
                # Store full document mapping
                url_to_full_document[file_url] = content
                
                # Extract code examples if enabled
                # Note: For source code files (.dml, .py), we skip markdown-style code block extraction
                # since the entire file is already code. The AST chunks provide well-structured code segments.
                # Code example extraction is designed for markdown documentation files.
                if agentic_rag_enabled:
                    # Skip code example extraction for source code files
                    # The AST-aware chunks already provide meaningful code segments
                    logging.debug(f"    ℹ️  Skipping code example extraction for source file (using AST chunks instead)")
                    pass
            
            if urls:
                # Update source information first
                source_summary = f"{source_id} source code containing {len(set(urls))} files"
                total_chars = sum(len(content) for content in contents)
                update_source_info(client, source_id, source_summary, total_chars // 4)  # Rough word estimate
                
                # Add documents to Supabase
                logging.info(f"  💾 Storing {len(contents)} document chunks...")
                add_documents_to_supabase(client, urls, chunk_numbers, contents, metadatas, url_to_full_document, delete_existing)
                
                # Note: Code examples are not extracted from source code files
                # The AST chunks already provide well-structured, searchable code segments
        
        logging.info(f"\n✅ Successfully added all source files to Supabase!")
        
    except Exception as e:
        logging.error(f"❌ Error adding source files to Supabase: {e}")
        import traceback
        traceback.print_exc()

async def crawl_simics_source(delete_existing: bool = True):
    """Main function to crawl Simics source code."""
    # Get Simics path from environment
    simics_path = os.getenv("SIMICS_SOURCE_PATH", "simics-7-packages-2025-38-linux64/")
    
    start_time = time.time()
    logging.info(f"🚀 Starting Simics Source Code Crawling at {datetime.now().strftime('%H:%M:%S')}")
    logging.info(f"📁 Simics path: {simics_path}")
    logging.info("")
    
    # Find source files
    source_files = find_simics_source_files(simics_path)
    total_files = len(source_files['dml']) + len(source_files['python'])
    
    if total_files == 0:
        logging.error("❌ No source files found. Check SIMICS_SOURCE_PATH setting.")
        return False
    
    logging.info(f"\n📋 Processing {total_files} source files...")
    
    # Process all files
    processed_files = []
    success_count = 0
    file_index = 0
    processing_start_time = time.time()
    
    def log_progress_and_eta(current_file, total_files, start_time):
        if current_file > 0:
            elapsed = time.time() - start_time
            avg_time_per_file = elapsed / current_file
            remaining_files = total_files - current_file
            eta_seconds = remaining_files * avg_time_per_file
            eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s" if eta_seconds > 60 else f"{int(eta_seconds)}s"
            progress_pct = (current_file / total_files) * 100
            logging.info(f"   📈 Progress: {current_file}/{total_files} ({progress_pct:.1f}%) | ETA: {eta_str} | Avg: {avg_time_per_file:.2f}s/file")
    
    # Process DML files
    if source_files['dml']:
        logging.info(f"\n🔧 Processing {len(source_files['dml'])} DML files...")
        for i, dml_file in enumerate(source_files['dml'], 1):
            file_index += 1
            result = process_source_file(dml_file, file_index, total_files)
            if result:
                processed_files.append(result)
                success_count += 1
            
            # Log progress every 10 files or on important milestones
            if file_index % 10 == 0 or file_index == total_files or i == len(source_files['dml']):
                log_progress_and_eta(file_index, total_files, processing_start_time)
    
    # Process Python files
    if source_files['python']:
        logging.info(f"\n🐍 Processing {len(source_files['python'])} Python files...")
        for i, py_file in enumerate(source_files['python'], 1):
            file_index += 1
            result = process_source_file(py_file, file_index, total_files)
            if result:
                processed_files.append(result)
                success_count += 1
            
            # Log progress every 10 files or on important milestones
            if file_index % 10 == 0 or file_index == total_files or i == len(source_files['python']):
                log_progress_and_eta(file_index, total_files, processing_start_time)
    
    processing_elapsed = time.time() - processing_start_time
    
    logging.info(f"\n📊 Processing Summary:")
    logging.info(f"   Total files found: {total_files}")
    logging.info(f"   Successfully processed: {success_count}")
    logging.info(f"   Failed: {total_files - success_count}")
    logging.info(f"   Processing time: {int(processing_elapsed // 60)}m {int(processing_elapsed % 60)}s")
    logging.info(f"   Average time per file: {processing_elapsed / total_files:.2f}s")
    
    if processed_files:
        # Add to Supabase
        logging.info(f"\n💾 Starting database upload phase...")
        logging.info(f"   🔗 Using GitHub URLs for source file links")
        
        # Show sample URL if we have processed files
        if processed_files:
            sample_path = processed_files[0]['file_path']
            sample_url = get_github_url_for_file(sample_path, simics_path)
            logging.info(f"   🔍 Sample URL: {sample_url}")
        
        upload_start_time = time.time()
        await add_source_files_to_supabase(processed_files, simics_path, delete_existing)
        upload_elapsed = time.time() - upload_start_time
        
        total_elapsed = time.time() - start_time
        logging.info(f"\n⏱️ Timing Summary:")
        logging.info(f"   File processing: {int(processing_elapsed // 60)}m {int(processing_elapsed % 60)}s")
        logging.info(f"   Database upload: {int(upload_elapsed // 60)}m {int(upload_elapsed % 60)}s")
        logging.info(f"   Total runtime: {int(total_elapsed // 60)}m {int(total_elapsed % 60)}s")
        return True
    else:
        logging.error("❌ No files were successfully processed")
        return False

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

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Crawl Simics source code into RAG database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python crawl_simics_source.py
  python crawl_simics_source.py --log-file simics_crawl.log
  python crawl_simics_source.py --log-file logs/simics_$(date +%Y%m%d_%H%M%S).log
        """
    )
    parser.add_argument('--output-dir', help='Output directory (unused, for pipeline compatibility)')
    parser.add_argument('--log-file', '-l', help='Optional log file to save detailed output (with timestamps)')
    
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
        logger.info(f"Output dir: {args.output_dir or 'N/A'}")
        logger.info(f"Log file: {args.log_file}")
        logger.info(f"Delete existing records: {delete_existing}")
        logger.info("-" * 80)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if Simics source crawling is enabled
    if os.getenv("CRAWL_SIMICS_SOURCE", "false").lower() != "true":
        logging.warning("⚠️  Simics source crawling is disabled. Set CRAWL_SIMICS_SOURCE=true to enable.")
        return
    
    try:
        success = asyncio.run(crawl_simics_source(delete_existing))
        if success:
            logging.info("\n🎉 Simics source code crawling completed successfully!")
        else:
            logging.error("\n❌ Simics source code crawling failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.warning("\n⚠️  Crawling interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()