#!/usr/bin/env python3
"""
Debug script to understand why vector search returns 0 results.
"""

import os
import sys
# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import get_supabase_client, search_documents, create_embedding

def check_database_state():
    """Check what's actually in the database."""
    try:
        client = get_supabase_client()
        
        # 1. Check if there are any records in crawled_pages
        print("=== Checking crawled_pages table ===")
        count_result = client.table("crawled_pages").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        print(f"Total records in crawled_pages: {total_count}")
        
        if total_count > 0:
            # 2. Get a few sample records
            sample_result = client.table("crawled_pages").select("id, url, content, metadata, source_id").limit(3).execute()
            print(f"\nSample records:")
            for i, record in enumerate(sample_result.data):
                print(f"  Record {i+1}:")
                print(f"    ID: {record.get('id')}")
                print(f"    URL: {record.get('url')}")
                print(f"    Source ID: {record.get('source_id')}")
                print(f"    Content length: {len(record.get('content', ''))}")
                print(f"    Metadata: {record.get('metadata')}")
                print()
        
        # 3. Check if embeddings exist and are not null/zero
        print("=== Checking embeddings ===")
        embedding_check = client.table("crawled_pages").select("id, url").not_.is_("embedding", "null").limit(5).execute()
        print(f"Records with non-null embeddings: {len(embedding_check.data)}")
        
        if embedding_check.data:
            print("Sample records with embeddings:")
            for record in embedding_check.data[:3]:
                print(f"  ID {record['id']}: {record['url']}")
        
        # 4. Test a simple search
        print("\n=== Testing search function ===")
        test_query = "test documentation example"
        print(f"Testing search with query: '{test_query}'")
        
        # Create embedding for test
        print("Creating embedding...")
        query_embedding = create_embedding(test_query)
        print(f"Query embedding created: {len(query_embedding)} dimensions")
        print(f"First 5 values: {query_embedding[:5]}")
        print(f"Is all zeros? {all(v == 0.0 for v in query_embedding)}")
        
        # Direct RPC call to debug
        print("\nTesting direct RPC call...")
        try:
            params = {
                'query_embedding': query_embedding,
                'match_count': 5
            }
            direct_result = client.rpc('match_crawled_pages', params).execute()
            print(f"Direct RPC result: {len(direct_result.data)} results")
            
            if direct_result.data:
                for i, result in enumerate(direct_result.data):
                    print(f"  Result {i+1}: {result.get('url')} (similarity: {result.get('similarity')})")
            else:
                print("  No results from direct RPC call")
                
        except Exception as e:
            print(f"Error in direct RPC call: {e}")
        
        # Test using the search_documents function
        print("\nTesting search_documents function...")
        search_results = search_documents(client, test_query, match_count=5)
        print(f"search_documents result: {len(search_results)} results")
        
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not check_database_state():
        sys.exit(1)