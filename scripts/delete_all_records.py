#!/usr/bin/env python3
"""
Script to delete all records from the crawled_pages, sources, and code_examples tables in Supabase.
WARNING: This will permanently delete all data!
"""

import os
import sys

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import get_supabase_client

def delete_records_by_source_id(source_id: str, auto_confirm: bool = False):
    """Delete all records associated with a specific source_id."""
    try:
        client = get_supabase_client()
        
        print(f"=== Checking Records for Source ID: {source_id} ===")
        
        # Check records in each table for this source_id
        tables_to_clean = ["crawled_pages", "sources", "code_examples"]
        table_counts = {}
        total_records = 0
        
        for table in tables_to_clean:
            try:
                if table == "sources":
                    # For sources table, match the source_id directly
                    count_result = client.table(table).select("source_id", count="exact").eq("source_id", source_id).execute()
                else:
                    # For other tables, they should have a source_id foreign key
                    count_result = client.table(table).select("id", count="exact").eq("source_id", source_id).execute()
                
                table_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                table_counts[table] = table_count
                total_records += table_count
                print(f"Found {table_count} records in {table} table for source_id: {source_id}")
            except Exception as e:
                print(f"Error checking {table} table: {e}")
                table_counts[table] = 0
        
        if total_records == 0:
            print(f"No records found for source_id: {source_id}")
            return True
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will DELETE {total_records} records for source_id: {source_id}")
        print("Records that will be deleted:")
        for table, count in table_counts.items():
            if count > 0:
                print(f"  - {table}: {count} records")
        print("\nThis action cannot be undone.")
        
        if auto_confirm:
            print("🤖 Auto-confirming deletion (--confirm flag)")
        else:
            response = input(f"Are you sure you want to delete all records for source_id '{source_id}'? Type 'DELETE' to confirm: ")
            if response != "DELETE":
                print("Operation cancelled.")
                return False
        
        print(f"\nDeleting records for source_id: {source_id}...")
        
        # Delete records from each table in proper order (handle foreign key constraints)
        deletion_order = ["code_examples", "crawled_pages", "sources"]
        
        total_deleted = 0
        
        for table in deletion_order:
            if table_counts.get(table, 0) == 0:
                print(f"\n📋 Skipping {table} (no records for this source_id)")
                continue
                
            print(f"\n📋 Deleting records from {table} for source_id: {source_id}...")
            
            try:
                if table == "sources":
                    # Delete from sources table using source_id
                    delete_result = client.table(table).delete().eq("source_id", source_id).execute()
                else:
                    # Delete from other tables using source_id foreign key
                    delete_result = client.table(table).delete().eq("source_id", source_id).execute()
                
                deleted_count = len(delete_result.data) if delete_result.data else 0
                total_deleted += deleted_count
                print(f"  ✅ Deleted {deleted_count} records from {table}")
                
            except Exception as e:
                print(f"  ❌ Error deleting from {table}: {e}")
        
        # Verify deletion
        print(f"\n🔍 Verifying deletion for source_id: {source_id}...")
        remaining_total = 0
        for table in tables_to_clean:
            try:
                if table == "sources":
                    verify_result = client.table(table).select("source_id", count="exact").eq("source_id", source_id).execute()
                else:
                    verify_result = client.table(table).select("id", count="exact").eq("source_id", source_id).execute()
                
                remaining_count = verify_result.count if hasattr(verify_result, 'count') else len(verify_result.data)
                remaining_total += remaining_count
                
                if remaining_count > 0:
                    print(f"⚠️  {table}: {remaining_count} records still remain")
                else:
                    print(f"✅ {table}: all records for source_id deleted")
            except Exception as e:
                print(f"Error verifying {table}: {e}")
        
        if remaining_total == 0:
            print(f"\n🎉 Successfully deleted all {total_deleted} records for source_id: {source_id}")
        else:
            print(f"\n⚠️  Warning: {remaining_total} records still remain for source_id: {source_id}")
            
        return remaining_total == 0
        
    except Exception as e:
        print(f"❌ Error deleting records for source_id {source_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def delete_all_records(auto_confirm: bool = False):
    """Delete all records from crawled_pages, sources, and code_examples tables."""
    try:
        client = get_supabase_client()
        
        print("=== Checking All Tables ===")
        
        # Check all tables
        tables_to_clean = ["crawled_pages", "sources", "code_examples"]
        table_counts = {}
        total_all_records = 0
        
        for table in tables_to_clean:
            try:
                # Different tables may have different primary key column names
                if table == "sources":
                    # Try common primary key names for sources table
                    try:
                        count_result = client.table(table).select("source_id", count="exact").execute()
                        primary_key = "source_id"
                    except:
                        try:
                            count_result = client.table(table).select("id", count="exact").execute()
                            primary_key = "id"
                        except:
                            # If both fail, try to get any column to count records
                            count_result = client.table(table).select("*", count="exact").execute()
                            primary_key = None
                else:
                    count_result = client.table(table).select("id", count="exact").execute()
                    primary_key = "id"
                
                table_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
                table_counts[table] = table_count
                total_all_records += table_count
                print(f"Found {table_count} records in {table} table")
            except Exception as e:
                print(f"Error checking {table} table: {e}")
                table_counts[table] = 0
        
        print(f"\nTotal records across all tables: {total_all_records}")
        
        if total_all_records == 0:
            print("All tables are already empty!")
            return True
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will DELETE ALL {total_all_records} records from ALL tables!")
        print("Tables that will be cleared:")
        for table, count in table_counts.items():
            if count > 0:
                print(f"  - {table}: {count} records")
        print("\nThis action cannot be undone.")
        
        if auto_confirm:
            print("🤖 Auto-confirming deletion (--confirm flag)")
        else:
            response = input("Are you sure you want to continue? Type 'DELETE ALL' to confirm: ")
            if response != "DELETE ALL":
                print("Operation cancelled.")
                return False
        
        print("\nDeleting records from all tables...")
        
        # Delete records from each table
        # Note: Delete in order to handle foreign key constraints
        # Order: code_examples -> crawled_pages -> sources (sources should be last as other tables reference it)
        deletion_order = ["code_examples", "crawled_pages", "sources"]
        
        # Define primary key columns for each table
        table_primary_keys = {
            "crawled_pages": "id",
            "code_examples": "id", 
            "sources": "source_id"  # sources table uses source_id as primary key
        }
        
        batch_size = 1000
        grand_total_deleted = 0
        
        for table in deletion_order:
            if table_counts.get(table, 0) == 0:
                print(f"\n📋 Skipping {table} (already empty)")
                continue
                
            print(f"\n📋 Deleting records from {table}...")
            table_deleted = 0
            
            while True:
                try:
                    # Get the correct primary key column for this table
                    pk_column = table_primary_keys.get(table, "id")
                    
                    # Get a batch of IDs to delete
                    batch_result = client.table(table).select(pk_column).limit(batch_size).execute()
                    
                    if not batch_result.data:
                        break  # No more records
                        
                    # Extract IDs from the batch
                    ids_to_delete = [record[pk_column] for record in batch_result.data]
                    
                    # Delete this batch
                    # For sources table, use more aggressive deletion
                    if table == "sources":
                        try:
                            # First try normal batch delete using correct primary key
                            delete_result = client.table(table).delete().in_(pk_column, ids_to_delete).execute()
                        except Exception as batch_error:
                            print(f"    Batch delete failed for sources: {batch_error}")
                            print(f"    Trying individual deletion for {len(ids_to_delete)} sources...")
                            # Try to delete each source individually
                            deleted_count = 0
                            for source_id in ids_to_delete:
                                try:
                                    individual_delete = client.table(table).delete().eq(pk_column, source_id).execute()
                                    if individual_delete.data:
                                        deleted_count += len(individual_delete.data)
                                except Exception as e:
                                    print(f"      Warning: Could not delete source {source_id}: {e}")
                            # Create a mock result object
                            delete_result = type('MockResult', (object,), {'data': [{}] * deleted_count})()
                    else:
                        delete_result = client.table(table).delete().in_(pk_column, ids_to_delete).execute()
                    
                    deleted_count = len(delete_result.data) if delete_result.data else len(ids_to_delete)
                    table_deleted += deleted_count
                    grand_total_deleted += deleted_count
                    
                    print(f"  Deleted {deleted_count} records from {table} (table total: {table_deleted})")
                    
                    # If we deleted fewer than batch_size, we're done with this table
                    if len(batch_result.data) < batch_size:
                        break
                        
                except Exception as e:
                    print(f"  Error deleting from {table}: {e}")
                    break
                    
            print(f"✅ Finished deleting from {table}: {table_deleted} records removed")
        
        # Verify deletion across all tables
        print(f"\n🔍 Verifying deletion...")
        final_total = 0
        for table in tables_to_clean:
            try:
                pk_column = table_primary_keys.get(table, "id")
                final_count_result = client.table(table).select(pk_column, count="exact").execute()
                final_count = final_count_result.count if hasattr(final_count_result, 'count') else len(final_count_result.data)
                final_total += final_count
                if final_count > 0:
                    print(f"⚠️  {table}: {final_count} records still remain")
                else:
                    print(f"✅ {table}: completely cleared")
            except Exception as e:
                print(f"Error verifying {table}: {e}")
        
        if final_total == 0:
            print(f"\n🎉 Successfully deleted all {grand_total_deleted} records from all tables!")
            print("Database is now completely empty and ready for fresh data.")
        else:
            print(f"\n⚠️  Warning: {final_total} total records still remain across all tables")
            
            # If sources table still has records, try a more aggressive cleanup
            for table in tables_to_clean:
                try:
                    pk_column = table_primary_keys.get(table, "id")
                    remaining_check = client.table(table).select(pk_column, count="exact").execute()
                    remaining_count = remaining_check.count if hasattr(remaining_check, 'count') else len(remaining_check.data)
                    
                    if remaining_count > 0 and table == "sources":
                        print(f"\n🔧 Attempting aggressive cleanup for sources table ({remaining_count} records)...")
                        
                        # Try to get all remaining source IDs and delete them one by one
                        remaining_sources = client.table("sources").select("source_id").execute()
                        if remaining_sources.data:
                            successful_deletes = 0
                            for source_record in remaining_sources.data:
                                try:
                                    force_delete = client.table("sources").delete().eq("source_id", source_record["source_id"]).execute()
                                    if force_delete.data:
                                        successful_deletes += len(force_delete.data)
                                except Exception as e:
                                    print(f"    Failed to force delete source {source_record['source_id']}: {e}")
                            
                            if successful_deletes > 0:
                                print(f"    ✅ Force deleted {successful_deletes} additional sources")
                                
                                # Re-check final count
                                final_sources_check = client.table("sources").select("source_id", count="exact").execute()
                                final_sources_count = final_sources_check.count if hasattr(final_sources_check, 'count') else len(final_sources_check.data)
                                
                                if final_sources_count == 0:
                                    print(f"    🎉 Sources table is now completely empty!")
                                else:
                                    print(f"    ⚠️  {final_sources_count} sources still remain (may be protected by constraints)")
                            
                except Exception as e:
                    print(f"Error during aggressive cleanup of {table}: {e}")
            
        # Final re-check
        try:
            final_recheck_total = 0
            for table in tables_to_clean:
                pk_column = table_primary_keys.get(table, "id")
                recheck_result = client.table(table).select(pk_column, count="exact").execute()
                recheck_count = recheck_result.count if hasattr(recheck_result, 'count') else len(recheck_result.data)
                final_recheck_total += recheck_count
            
            return final_recheck_total == 0
        except:
            return final_total == 0
        
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
    import argparse
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Delete records from Supabase database')
    parser.add_argument('--source-id', type=str, 
                       help='Delete records for a specific source_id only')
    parser.add_argument('--confirm', action='store_true',
                       help='Auto-confirm deletion without prompting')
    parser.add_argument('--list-sources', action='store_true',
                       help='List all available source_ids in the database')
    
    args = parser.parse_args()
    
    print("🗑️  Supabase Database Cleanup Tool")
    
    # List sources if requested
    if args.list_sources:
        try:
            client = get_supabase_client()
            sources_result = client.table("sources").select("*").execute()
            
            if sources_result.data:
                print(f"\nFound {len(sources_result.data)} sources in database:")
                print("-" * 80)
                for source in sources_result.data:
                    print(f"Source ID: {source.get('source_id', 'Unknown')}")
                    # Display all available columns except source_id
                    for key, value in source.items():
                        if key != 'source_id' and value is not None:
                            # Truncate long values for readability
                            display_value = str(value)
                            if len(display_value) > 70:
                                display_value = display_value[:70] + '...'
                            print(f"{key.title()}: {display_value}")
                    print("-" * 80)
            else:
                print("\nNo sources found in database.")
        except Exception as e:
            print(f"Error listing sources: {e}")
        sys.exit(0)
    
    # Delete by source_id if specified
    if args.source_id:
        print(f"Deleting records for source_id: {args.source_id}")
        success = delete_records_by_source_id(args.source_id, args.confirm)
    else:
        print("This script will delete ALL records from crawled_pages, sources, and code_examples tables.")
        print()
        success = delete_all_records(args.confirm)
        
        if not success:
            print("\nPrimary deletion method failed.")
            alternative_delete_method()
    
    if success:
        print("\nDone! You can now re-crawl your data with consistent embeddings.")
        print("Make sure your .env is configured with your preferred embedding method:")
        print("  USE_QWEN_EMBEDDINGS=false")
        print("  USE_COPILOT_EMBEDDINGS=true")
        print("Or:")
        print("  USE_QWEN_EMBEDDINGS=true") 
        print("  USE_COPILOT_EMBEDDINGS=false")
