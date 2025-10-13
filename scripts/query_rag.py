#!/usr/bin/env python3
"""
RAG Query Script - Query the crawled documentation database.
This script allows you to test your RAG system by querying the crawled content.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def query_documents(query: str, source_type: str = 'all', match_count: int = 5, use_hybrid: bool = False):
    """
    Query the document database.
    
    Args:
        query: Search query
        source_type: Source type filter ('docs', 'dml', 'python', 'source', 'all')
        match_count: Number of results to return
        use_hybrid: Whether to use hybrid search
        
    Returns:
        Search results
    """
    try:
        from utils import get_supabase_client, search_documents
        
        client = get_supabase_client()
        
        # Determine filter based on source_type - use source_id filtering like perform_rag_query
        filter_metadata = None
        non_simics_sources = None
        
        if source_type == 'docs':
            # For docs, search all non-simics sources by excluding simics-dml and simics-python
            # Get all available sources first, then filter out simics sources
            sources_result = client.from_('sources').select('source_id').execute()
            if sources_result.data:
                non_simics_sources = [s['source_id'] for s in sources_result.data 
                                    if s['source_id'] not in ['simics-dml', 'simics-python']]
                if non_simics_sources:
                    print(f"🎯 Documentation filter: searching {len(non_simics_sources)} non-simics sources (excludes simics-dml, simics-python)")
        elif source_type == 'dml':
            filter_metadata = {"source_id": "simics-dml"}
        elif source_type == 'python':
            filter_metadata = {"source_id": "simics-python"}
        elif source_type == 'source':
            # For simics sources, we'll search simics-dml and simics-python
            pass  # Will handle in multi-source section below
        
        print(f"🔍 Searching documents...")
        print(f"   Query: '{query}'")
        print(f"   Source type: {source_type}")
        print(f"   Match count: {match_count}")
        print(f"   Hybrid search: {'Yes' if use_hybrid else 'No'}")
        print()
        
        # Set environment variable for hybrid search if requested
        if use_hybrid:
            os.environ["USE_HYBRID_SEARCH"] = "true"
        
        # Handle multi-source search for 'source' and 'docs' types
        if source_type == 'source':
            # Search both simics-dml and simics-python sources
            all_results = []
            
            for source_id in ['simics-dml', 'simics-python']:
                source_filter_meta = {"source_id": source_id}
                source_results = search_documents(
                    client=client,
                    query=query,
                    match_count=match_count,
                    filter_metadata=source_filter_meta
                )
                all_results.extend(source_results)
                print(f"   🎯 Found {len(source_results)} results from {source_id}")
            
            # Sort by similarity and take top results
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            results = all_results[:match_count]
            print(f"   🔗 Combined results: {len(results)} total from simics sources")
        elif source_type == 'docs' and non_simics_sources:
            # Search all non-simics sources
            all_results = []
            
            for source_id in non_simics_sources:
                source_filter_meta = {"source_id": source_id}
                source_results = search_documents(
                    client=client,
                    query=query,
                    match_count=match_count,
                    filter_metadata=source_filter_meta
                )
                all_results.extend(source_results)
                print(f"   🎯 Found {len(source_results)} results from {source_id}")
            
            # Sort by similarity and take top results
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            results = all_results[:match_count]
            print(f"   🔗 Combined results: {len(results)} total from {len(non_simics_sources)} documentation sources")
        else:
            # Single source search
            results = search_documents(
                client=client,
                query=query,
                match_count=match_count,
                filter_metadata=filter_metadata
            )
        
        return results
        
    except Exception as e:
        print(f"❌ Error querying documents: {e}")
        import traceback
        traceback.print_exc()
        return []

def query_code_examples(query: str, source_filter: str = None, source_type: str = 'all', match_count: int = 5):
    """
    Query the code examples database.
    
    Args:
        query: Search query for code
        source_filter: Optional source domain filter (legacy)
        source_type: Source type filter ('docs', 'dml', 'python', 'source', 'all')
        match_count: Number of results to return
        
    Returns:
        Code example search results
    """
    try:
        from utils import get_supabase_client, search_code_examples
        
        client = get_supabase_client()
        
        # Determine filter based on source_type
        filter_metadata = None
        if source_type == 'docs':
            filter_metadata = {"source_id": "intel.github.io"}
        elif source_type == 'dml':
            filter_metadata = {"source_id": "simics-dml"}
        elif source_type == 'python':
            filter_metadata = {"source_id": "simics-python"}
        elif source_type == 'source':
            # Need to search multiple sources - we'll handle this differently
            filter_metadata = None  # Will filter after query
        elif source_filter:
            # Legacy source_filter parameter
            filter_metadata = {"source_id": source_filter}
        
        print(f"🔍 Searching code examples...")
        print(f"   Query: '{query}'")
        print(f"   Source type: {source_type}")
        print(f"   Match count: {match_count}")
        print()
        
        results = search_code_examples(
            client=client,
            query=query,
            match_count=match_count,
            filter_metadata=filter_metadata
        )
        
        # Post-filter for 'source' type (both DML and Python)
        if source_type == 'source':
            results = [r for r in results if r.get('metadata', {}).get('source_id') in ['simics-dml', 'simics-python']]
            # Single source search
            results = search_code_examples(
                client=client,
                query=query,
                match_count=match_count,
                filter_metadata=filter_metadata
            )
        
        return results
        
    except Exception as e:
        print(f"❌ Error querying code examples: {e}")
        import traceback
        traceback.print_exc()
        return []

def display_document_results(results: list):
    """Display document search results in a readable format."""
    if not results:
        print("📭 No documents found.")
        return
    
    print(f"📄 Found {len(results)} document(s):")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n🔸 Result #{i}")
        print(f"   📍 URL: {result.get('url', 'Unknown')}")
        print(f"   📊 Similarity: {result.get('similarity', 0):.4f}")
        if result.get('rerank_score'):
            print(f"   🎯 Rerank Score: {result.get('rerank_score'):.4f}")
        print(f"   📦 Chunk #{result.get('chunk_number', 'Unknown')}")
        
        content = result.get('content', '')
        if len(content) > 300:
            content = content[:300] + "..."
        print(f"   📝 Content: {content}")
        
        metadata = result.get('metadata', {})
        if metadata:
            print(f"   🏷️  Metadata: {json.dumps(metadata, indent=6)}")

def display_code_results(results: list):
    """Display code example search results in a readable format."""
    if not results:
        print("📭 No code examples found.")
        return
    
    print(f"💻 Found {len(results)} code example(s):")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n🔸 Code Example #{i}")
        print(f"   📍 URL: {result.get('url', 'Unknown')}")
        print(f"   📊 Similarity: {result.get('similarity', 0):.4f}")
        if result.get('rerank_score'):
            print(f"   🎯 Rerank Score: {result.get('rerank_score'):.4f}")
        
        summary = result.get('summary', '')
        if summary:
            print(f"   📝 Summary: {summary}")
        
        code = result.get('code_example', '')
        if code:
            # Show first 500 characters of code
            if len(code) > 500:
                code_display = code[:500] + "\n... (truncated)"
            else:
                code_display = code
            print(f"   💻 Code:")
            print("   " + "-" * 40)
            # Indent each line of code
            for line in code_display.split('\n'):
                print(f"   {line}")
            print("   " + "-" * 40)
        
        metadata = result.get('metadata', {})
        if metadata:
            relevant_meta = {k: v for k, v in metadata.items() 
                           if k in ['language', 'code_length', 'chunk_index']}
            if relevant_meta:
                print(f"   🏷️  Metadata: {json.dumps(relevant_meta, indent=6)}")

def get_available_sources():
    """Get list of available sources in the database."""
    try:
        from utils import get_supabase_client
        
        client = get_supabase_client()
        
        # Get sources from the sources table, just like other functions do
        sources_result = client.from_('sources').select('source_id').execute()
        if sources_result.data:
            all_sources = [s['source_id'] for s in sources_result.data]
            return sorted(all_sources)
        else:
            return []
        
    except Exception as e:
        print(f"❌ Error getting sources: {e}")
        return []

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Query the RAG database')
    parser.add_argument('query', nargs='?', help='Search query (required unless --list-sources)')
    parser.add_argument('--count', '-c', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--type', '-t', choices=['docs', 'code', 'both'], default='docs',
                       help='Search type: docs, code, or both (default: docs)')
    parser.add_argument('--source-type', choices=['docs', 'dml', 'python', 'source', 'all'], default='all',
                       help='Filter by source type: docs (non-simics sources), dml (simics-dml), python (simics-python), source (dml+python), or all (default: all)')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid search for documents')
    parser.add_argument('--list-sources', action='store_true', help='List available sources and exit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # List sources if requested
    if args.list_sources:
        print("📋 Available sources in database:")
        sources = get_available_sources()
        if sources:
            for source in sources:
                print(f"   • {source}")
        else:
            print("   No sources found")
        return
    
    if not args.query:
        print("❌ Error: Query is required unless using --list-sources")
        parser.print_help()
        return
    
    # Show configuration if verbose
    if args.verbose:
        print("⚙️  Configuration:")
        print(f"   Embedding provider: {os.getenv('USE_QWEN_EMBEDDINGS', 'false') == 'true' and 'Qwen' or 'OpenAI/Copilot'}")
        print(f"   Reranking: {os.getenv('USE_RERANKING', 'false')}")
        print(f"   Agentic RAG: {os.getenv('USE_AGENTIC_RAG', 'false')}")
        print()
    
    # Perform searches based on type
    if args.type in ['docs', 'both']:
        print("🔍 DOCUMENT SEARCH")
        print("=" * 50)
        doc_results = query_documents(
            query=args.query,
            source_type=args.source_type,
            match_count=args.count,
            use_hybrid=args.hybrid
        )
        display_document_results(doc_results)
    
    if args.type in ['code', 'both']:
        if args.type == 'both':
            print("\n\n")
        
        print("💻 CODE EXAMPLE SEARCH")
        print("=" * 50)
        code_results = query_code_examples(
            query=args.query,
            source_filter=args.source,
            source_type=args.source_type,
            match_count=args.count
        )
        display_code_results(code_results)
    
    # Summary
    if args.type == 'both':
        doc_count = len(doc_results) if 'doc_results' in locals() else 0
        code_count = len(code_results) if 'code_results' in locals() else 0
        print(f"\n📊 Summary: Found {doc_count} documents and {code_count} code examples")

if __name__ == "__main__":
    main()