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
                ('code_examples', 'id')
            ]
            for table, primary_key in table_configs:
                try:
                    result = self._client.table(table).select(primary_key, count='exact').execute()
                    stats['tables'][table] = result.count
                except Exception:
                    stats['tables'][table] = 'Error'
        
        return stats
    
    def list_collections(self) -> List[str]:
        """List all tables in Supabase."""
        return ['sources', 'crawled_pages', 'code_examples']
    
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