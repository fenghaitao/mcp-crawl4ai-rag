#!/usr/bin/env python3
"""
Debug script to check embeddings in detail.
"""

import os
import sys
# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import get_supabase_client, create_embedding

def check_embeddings_detailed():
    """Check embeddings in detail."""
    try:
        client = get_supabase_client()
        
        # 1. Check how many records have null vs non-null embeddings
        print("=== Embedding Statistics ===")
        
        # Count null embeddings
        null_result = client.table("crawled_pages").select("id", count="exact").is_("embedding", "null").execute()
        null_count = null_result.count if hasattr(null_result, 'count') else len(null_result.data)
        print(f"Records with NULL embeddings: {null_count}")
        
        # Count non-null embeddings
        non_null_result = client.table("crawled_pages").select("id", count="exact").not_.is_("embedding", "null").execute()
        non_null_count = non_null_result.count if hasattr(non_null_result, 'count') else len(non_null_result.data)
        print(f"Records with non-NULL embeddings: {non_null_count}")
        
        # 2. Get sample records with embeddings to examine them
        print("\n=== Sample Embeddings ===")
        sample_with_embeddings = client.table("crawled_pages").select("id, url, content, embedding").not_.is_("embedding", "null").limit(3).execute()
        
        for i, record in enumerate(sample_with_embeddings.data):
            print(f"\nRecord {i+1} (ID: {record['id']}):")
            print(f"  URL: {record['url']}")
            print(f"  Content preview: {record['content'][:100]}...")
            
            embedding = record['embedding']
            if embedding:
                print(f"  Embedding length: {len(embedding)}")
                print(f"  First 5 values: {embedding[:5]}")
                print(f"  All zeros? {all(v == 0.0 for v in embedding)}")
                print(f"  Has any non-zero? {any(v != 0.0 for v in embedding)}")
            else:
                print("  Embedding: None")
        
        # 3. Try a direct search with specific parameters to debug
        print("\n=== Direct Search Debug ===")
        
        # Create a test embedding
        test_query = "simics"  # Based on the URLs we saw
        query_embedding = create_embedding(test_query)
        print(f"Test query: '{test_query}'")
        print(f"Query embedding first 5: {query_embedding[:5]}")
        
        # Try direct search without any filters
        try:
            params = {
                'query_embedding': query_embedding,
                'match_count': 10
            }
            result1 = client.rpc('match_crawled_pages', params).execute()
            print(f"Search without filters: {len(result1.data)} results")
            
            # Try with empty filter
            params['filter'] = {}
            result2 = client.rpc('match_crawled_pages', params).execute()
            print(f"Search with empty filter: {len(result2.data)} results")
            
            # Try with null source filter
            params['source_filter'] = None
            result3 = client.rpc('match_crawled_pages', params).execute()
            print(f"Search with null source filter: {len(result3.data)} results")
            
            if result1.data:
                print("First result:", result1.data[0])
            
        except Exception as e:
            print(f"Error in direct search: {e}")
        
        # 4. Check if the function exists and is callable
        print("\n=== Function Check ===")
        try:
            func_check = client.rpc('match_crawled_pages', {
                'query_embedding': [0.0] * 1536,
                'match_count': 1
            }).execute()
            print(f"Function is callable, returned {len(func_check.data)} results")
        except Exception as e:
            print(f"Function call error: {e}")
            
        return True
        
    except Exception as e:
        print(f"Error in detailed check: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not check_embeddings_detailed():
        sys.exit(1)