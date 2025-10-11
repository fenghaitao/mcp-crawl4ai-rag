#!/usr/bin/env python3
"""
Script to delete all records from the crawled_pages table in Supabase.
WARNING: This will permanently delete all data!
"""

import os
import sys

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import get_supabase_client

def delete_all_records():
    """Delete all records from crawled_pages table."""
    try:
        client = get_supabase_client()
        
        print("=== Deleting All Records from crawled_pages ===")
        
        # First, check how many records exist
        count_result = client.table("crawled_pages").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        print(f"Found {total_count} records in the database")
        
        if total_count == 0:
            print("Database is already empty!")
            return True
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will DELETE ALL {total_count} records!")
        print("This action cannot be undone.")
        response = input("Are you sure you want to continue? Type 'DELETE ALL' to confirm: ")
        
        if response != "DELETE ALL":
            print("Operation cancelled.")
            return False
        
        print("\nDeleting records...")
        
        # Delete all records
        # Note: Supabase doesn't have a direct "delete all" without a condition
        # We'll delete in batches to avoid timeout issues
        
        batch_size = 1000
        deleted_total = 0
        
        while True:
            # Get a batch of IDs to delete
            batch_result = client.table("crawled_pages").select("id").limit(batch_size).execute()
            
            if not batch_result.data:
                break  # No more records
                
            # Extract IDs from the batch
            ids_to_delete = [record['id'] for record in batch_result.data]
            
            # Delete this batch
            delete_result = client.table("crawled_pages").delete().in_("id", ids_to_delete).execute()
            
            deleted_count = len(delete_result.data) if delete_result.data else len(ids_to_delete)
            deleted_total += deleted_count
            
            print(f"Deleted {deleted_count} records (total: {deleted_total})")
            
            # If we deleted fewer than batch_size, we're done
            if len(batch_result.data) < batch_size:
                break
        
        # Verify deletion
        final_count_result = client.table("crawled_pages").select("id", count="exact").execute()
        final_count = final_count_result.count if hasattr(final_count_result, 'count') else len(final_count_result.data)
        
        if final_count == 0:
            print(f"✅ Successfully deleted all {deleted_total} records!")
            print("Database is now empty and ready for fresh data.")
        else:
            print(f"⚠️  Warning: {final_count} records still remain in the database")
            
        return final_count == 0
        
    except Exception as e:
        print(f"❌ Error deleting records: {e}")
        import traceback
        traceback.print_exc()
        return False

def alternative_delete_method():
    """Alternative method using raw SQL if the batch method doesn't work."""
    try:
        client = get_supabase_client()
        
        print("\n=== Alternative: Using SQL TRUNCATE ===")
        print("This will use SQL TRUNCATE to quickly delete all records.")
        
        response = input("Try SQL TRUNCATE method? (y/N): ")
        if response.lower() != 'y':
            return False
            
        # Try using RPC to execute a truncate-like operation
        # Note: This might not work depending on Supabase permissions
        try:
            # This is a more direct approach but may require RPC function
            result = client.rpc('truncate_crawled_pages').execute()
            print("✅ Successfully truncated table using SQL")
            return True
        except Exception as e:
            print(f"SQL truncate failed: {e}")
            print("You may need to manually run: TRUNCATE TABLE crawled_pages;")
            return False
            
    except Exception as e:
        print(f"Error with alternative method: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🗑️  Supabase Database Cleanup Tool")
    print("This script will delete ALL records from the crawled_pages table.")
    print()
    
    success = delete_all_records()
    
    if not success:
        print("\nPrimary deletion method failed.")
        alternative_delete_method()
    
    print("\nDone! You can now re-crawl your data with consistent embeddings.")
    print("Make sure your .env is configured with your preferred embedding method:")
    print("  USE_QWEN_EMBEDDINGS=false")
    print("  USE_COPILOT_EMBEDDINGS=true")
    print("Or:")
    print("  USE_QWEN_EMBEDDINGS=true") 
    print("  USE_COPILOT_EMBEDDINGS=false")
