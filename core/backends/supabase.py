"""
Supabase database backend implementation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from .base import DatabaseBackend


class SupabaseBackend(DatabaseBackend):
    """Supabase database backend implementation."""
    
    def __init__(self):
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        try:
            # Import from server utils
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))
            from utils import get_supabase_client
            self._client = get_supabase_client()
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Supabase client: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Supabase database statistics."""
        stats = {
            'backend': 'supabase',
            'url': os.getenv('SUPABASE_URL', 'Not configured'),
            'connected': self.is_connected(),
            'tables': {}
        }
        
        if self.is_connected():
            # Get table counts - use correct primary key for each table
            table_configs = [
                ('sources', 'source_id'),
                ('crawled_pages', 'id'),
                ('code_examples', 'id'),
                ('files', 'id'),                    # Add new tables
                ('content_chunks', 'id')            # Add new tables
            ]
            for table, primary_key in table_configs:
                try:
                    result = self._client.table(table).select(primary_key, count='exact').execute()
                    stats['tables'][table] = result.count
                except Exception as e:
                    # Better error handling - show if table doesn't exist
                    if "does not exist" in str(e).lower() or "table" in str(e).lower():
                        stats['tables'][table] = 'Table not found'
                    else:
                        stats['tables'][table] = f'Error: {str(e)[:50]}...'
        
        return stats
    
    def list_collections(self) -> List[str]:
        """List all tables in Supabase."""
        return ['sources', 'crawled_pages', 'code_examples', 'files', 'content_chunks']
    
    def delete_collection(self, name: str) -> bool:
        """Delete all records from a specific table."""
        try:
            self._client.table(name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            return True
        except Exception:
            return False
    
    def delete_all_data(self) -> bool:
        """Delete all data from all tables."""
        success = True
        for table in self.list_collections():
            if not self.delete_collection(table):
                success = False
        return success
    
    def is_connected(self) -> bool:
        """Check if Supabase connection is active."""
        return self._client is not None
    
    def get_backend_name(self) -> str:
        """Get backend name."""
        return "supabase"
    
    def get_config_info(self) -> Dict[str, str]:
        """Get Supabase configuration information."""
        supabase_url = os.getenv('SUPABASE_URL', 'Not set')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY', 'Not set')
        
        return {
            'URL': supabase_url,
            'Service Key': '✅ Set' if supabase_key != 'Not set' else '❌ Not set',
            'Connection': '✅ Active' if self.is_connected() else '❌ Failed'
        }
    
    def apply_schema(self, schema_files: List[str]) -> bool:
        """Apply SQL schema files to Supabase database."""
        if not self.is_connected():
            raise ConnectionError("Not connected to Supabase")
        
        print("⚠️  For Supabase schema application:")
        print("   1. Copy the SQL content from the schema files")
        print("   2. Go to your Supabase Dashboard → SQL Editor")
        print("   3. Paste and execute each SQL file manually")
        print("   4. This ensures proper permissions and execution")
        
        # For now, we'll show the SQL content instead of executing it
        for schema_file in schema_files:
            try:
                with open(schema_file, 'r') as f:
                    sql_content = f.read()
                
                print(f"\n📄 Content of {schema_file}:")
                print("-" * 50)
                print(sql_content)
                print("-" * 50)
                        
            except Exception as e:
                print(f"Error reading {schema_file}: {e}")
                return False
        
        print("\n✅ Schema files displayed. Please apply them manually in Supabase Dashboard.")
        return True
    
    def drop_schema(self, table_names: List[str]) -> bool:
        """Drop tables from Supabase database."""
        if not self.is_connected():
            raise ConnectionError("Not connected to Supabase")
        
        print("⚠️  For Supabase schema dropping:")
        print("   1. Go to your Supabase Dashboard → SQL Editor")
        print("   2. Execute the following DROP statements:")
        
        for table_name in table_names:
            drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            print(f"   {drop_sql}")
        
        print("\n✅ Schema drop commands displayed. Please execute them manually in Supabase Dashboard.")
        return True