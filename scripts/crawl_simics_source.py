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
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def find_simics_source_files(simics_path: str) -> Dict[str, List[str]]:
    """Find DML and Python files in Simics packages."""
    simics_path = Path(simics_path)
    
    if not simics_path.exists():
        logging.error(f"❌ Simics path not found: {simics_path}")
        return {'dml': [], 'python': []}
    
    logging.info(f"🔍 Searching for source files in: {simics_path}")
    
    # Find DML files
    dml_files = list(simics_path.rglob("*.dml"))
    logging.info(f"   Found {len(dml_files)} DML files")
    
    # Find Python files
    python_files = list(simics_path.rglob("*.py"))
    logging.info(f"   Found {len(python_files)} Python files")
    
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

def process_source_file(file_path: str) -> Dict[str, Any]:
    """Process a single source file."""
    try:
        logging.info(f"  📄 Processing: {Path(file_path).name}")
        
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

async def add_source_files_to_supabase(processed_files: List[Dict[str, Any]], delete_existing: bool = True):
    """Add processed source files to Supabase."""
    try:
        from utils import get_supabase_client, add_documents_to_supabase
        from utils import extract_code_blocks, generate_code_example_summary, add_code_examples_to_supabase
        from utils import update_source_info, extract_source_summary
        
        # Import smart_chunk_markdown from crawl4ai_mcp
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from crawl4ai_mcp import smart_chunk_markdown
        from urllib.parse import urlparse
        from concurrent.futures import ThreadPoolExecutor
        
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
        for source_id, files in files_by_source.items():
            logging.info(f"\n📁 Processing {len(files)} files for source: {source_id}")
            
            # Prepare data for batch insertion
            urls = []
            chunk_numbers = []
            contents = []
            metadatas = []
            url_to_full_document = {}
            
            # Prepare code example data
            all_code_urls = []
            all_code_chunk_numbers = []
            all_code_examples = []
            all_code_summaries = []
            all_code_metadatas = []
            
            for file_data in files:
                file_path = file_data['file_path']
                content = file_data['content']
                metadata = file_data['metadata']
                
                # Create file:// URL for the source file
                file_url = f"file://{os.path.abspath(file_path)}"
                
                # Chunk the content
                chunks = smart_chunk_markdown(content)
                logging.info(f"  📦 {Path(file_path).name}: {len(chunks)} chunks")
                
                # Add chunks for document storage
                for i, chunk in enumerate(chunks):
                    urls.append(file_url)
                    chunk_numbers.append(i)
                    contents.append(chunk)
                    
                    # Enhance metadata with chunk info
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        "chunk_index": i,
                        "url": file_url,
                        "source": source_id,
                        "crawl_time": "simics_source_crawl"
                    })
                    metadatas.append(chunk_metadata)
                
                # Store full document mapping
                url_to_full_document[file_url] = content
                
                # Extract code examples if enabled
                if agentic_rag_enabled:
                    try:
                        code_blocks = extract_code_blocks(content)
                        if code_blocks:
                            logging.info(f"    🔬 Found {len(code_blocks)} code blocks")
                            
                            # Generate summaries for code examples
                            def process_code_example(args):
                                code, context_before, context_after = args
                                return generate_code_example_summary(code, context_before, context_after)
                            
                            summary_args = [
                                (block['code'], block['context_before'], block['context_after'])
                                for block in code_blocks
                            ]
                            
                            with ThreadPoolExecutor(max_workers=3) as executor:
                                summaries = list(executor.map(process_code_example, summary_args))
                            
                            # Add to code examples batch
                            for i, (block, summary) in enumerate(zip(code_blocks, summaries)):
                                all_code_urls.append(file_url)
                                all_code_chunk_numbers.append(i)
                                all_code_examples.append(block['code'])
                                all_code_summaries.append(summary)
                                
                                # Create metadata for code example
                                code_meta = metadata.copy()
                                code_meta.update({
                                    "chunk_index": i,
                                    "url": file_url,
                                    "source": source_id,
                                    "code_length": len(block['code']),
                                    "block_type": block.get('type', 'unknown')
                                })
                                all_code_metadatas.append(code_meta)
                        
                    except Exception as e:
                        logging.warning(f"    ⚠️  Error extracting code examples: {e}")
            
            if urls:
                # Update source information first
                source_summary = f"{source_id} source code containing {len(set(urls))} files"
                total_chars = sum(len(content) for content in contents)
                update_source_info(client, source_id, source_summary, total_chars // 4)  # Rough word estimate
                
                # Add documents to Supabase
                logging.info(f"  💾 Storing {len(contents)} document chunks...")
                add_documents_to_supabase(client, urls, chunk_numbers, contents, metadatas, url_to_full_document, delete_existing)
                
                # Add code examples if any
                if agentic_rag_enabled and all_code_examples:
                    logging.info(f"  🔬 Storing {len(all_code_examples)} code examples...")
                    add_code_examples_to_supabase(
                        client,
                        all_code_urls,
                        all_code_chunk_numbers,
                        all_code_examples,
                        all_code_summaries,
                        all_code_metadatas,
                        delete_existing
                    )
        
        logging.info(f"\n✅ Successfully added all source files to Supabase!")
        
    except Exception as e:
        logging.error(f"❌ Error adding source files to Supabase: {e}")
        import traceback
        traceback.print_exc()

async def crawl_simics_source(delete_existing: bool = True):
    """Main function to crawl Simics source code."""
    # Get Simics path from environment
    simics_path = os.getenv("SIMICS_SOURCE_PATH", "simics-7-packages-2025-38-linux64/")
    
    logging.info(f"🚀 Starting Simics Source Code Crawling")
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
    
    # Process DML files
    if source_files['dml']:
        logging.info(f"\n🔧 Processing {len(source_files['dml'])} DML files...")
        for dml_file in source_files['dml']:
            result = process_source_file(dml_file)
            if result:
                processed_files.append(result)
                success_count += 1
    
    # Process Python files
    if source_files['python']:
        logging.info(f"\n🐍 Processing {len(source_files['python'])} Python files...")
        for py_file in source_files['python']:
            result = process_source_file(py_file)
            if result:
                processed_files.append(result)
                success_count += 1
    
    logging.info(f"\n📊 Processing Summary:")
    logging.info(f"   Total files found: {total_files}")
    logging.info(f"   Successfully processed: {success_count}")
    logging.info(f"   Failed: {total_files - success_count}")
    
    if processed_files:
        # Add to Supabase
        await add_source_files_to_supabase(processed_files, delete_existing)
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