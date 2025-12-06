"""
Supabase database backend implementation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

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
        
        # Auto-detection: execute locally, display for cloud
        if self._is_local_supabase():
            return self._execute_sql_via_docker(schema_files)
        else:
            return self._display_sql_for_manual_execution(schema_files)
    
    def _is_local_supabase(self) -> bool:
        """Detect if this is a local Supabase instance."""
        supabase_url = os.getenv('SUPABASE_URL', '')
        return 'localhost' in supabase_url or '127.0.0.1' in supabase_url
    
    def _execute_sql_via_docker(self, schema_files: List[str]) -> bool:
        """Execute SQL files directly via Docker for local Supabase."""
        import subprocess
        
        print("🐳 Local Supabase detected - executing SQL directly via Docker...")
        
        success = True
        for schema_file in schema_files:
            try:
                print(f"\n📄 Executing {schema_file}...")
                
                # Read SQL content
                with open(schema_file, 'r') as f:
                    sql_content = f.read()
                
                # Execute via Docker
                result = subprocess.run([
                    'docker', 'exec', '-i', 'supabase-db',
                    'psql', '-U', 'postgres', '-d', 'postgres'
                ], input=sql_content, text=True, capture_output=True)
                
                if result.returncode == 0:
                    print(f"✅ {schema_file} applied successfully")
                    if result.stdout.strip():
                        print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"❌ Error in {schema_file}: {result.stderr}")
                    success = False
                        
            except Exception as e:
                print(f"❌ Error applying {schema_file}: {e}")
                success = False
        
        if success:
            print("\n🎉 All schema files applied successfully to local Supabase!")
        else:
            print("\n⚠️  Some schema files failed to apply.")
        
        return success
    
    def _display_sql_for_manual_execution(self, schema_files: List[str]) -> bool:
        """Display SQL content for manual execution in cloud Supabase."""
        print("☁️  Cloud Supabase detected - displaying SQL for manual application:")
        print("   1. Copy the SQL content from the schema files")
        print("   2. Go to your Supabase Dashboard → SQL Editor")
        print("   3. Paste and execute each SQL file manually")
        print("   4. This ensures proper permissions and execution")
        
        # Show the SQL content for manual copy/paste
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
        
        # Auto-detection: execute locally, display for cloud
        if self._is_local_supabase():
            return self._drop_tables_via_docker(table_names)
        else:
            return self._display_drop_commands_for_manual_execution(table_names)
    
    def _drop_tables_via_docker(self, table_names: List[str]) -> bool:
        """Drop tables directly via Docker for local Supabase."""
        import subprocess
        
        print("🐳 Local Supabase detected - dropping tables directly via Docker...")
        
        success = True
        for table_name in table_names:
            try:
                print(f"\n🗑️ Dropping table {table_name}...")
                
                drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
                
                # Execute via Docker
                result = subprocess.run([
                    'docker', 'exec', '-i', 'supabase-db',
                    'psql', '-U', 'postgres', '-d', 'postgres'
                ], input=drop_sql, text=True, capture_output=True)
                
                if result.returncode == 0:
                    print(f"✅ Table {table_name} dropped successfully")
                    if result.stdout.strip():
                        print(f"   Output: {result.stdout.strip()}")
                else:
                    print(f"❌ Error dropping {table_name}: {result.stderr}")
                    success = False
                        
            except Exception as e:
                print(f"❌ Error dropping {table_name}: {e}")
                success = False
        
        if success:
            print("\n🎉 All tables dropped successfully from local Supabase!")
        else:
            print("\n⚠️  Some tables failed to drop.")
        
        return success
    
    def _display_drop_commands_for_manual_execution(self, table_names: List[str]) -> bool:
        """Display DROP commands for manual execution in cloud Supabase."""
        print("☁️  Cloud Supabase detected - displaying DROP commands for manual execution:")
        print("   1. Go to your Supabase Dashboard → SQL Editor")
        print("   2. Execute the following DROP statements:")
        
        for table_name in table_names:
            drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE;"
            print(f"   {drop_sql}")
        
        print("\n✅ Schema drop commands displayed. Please execute them manually in Supabase Dashboard.")
        return True
    
    def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """Get dynamic schema information from Supabase database."""
        if not self.is_connected():
            return {}
        
        schema_info = {}
        
        # Use direct PostgreSQL queries for schema discovery
        if self._is_local_supabase():
            schema_info = self._get_schema_via_docker()
        else:
            # For cloud, fall back to basic table list with manual descriptions
            schema_info = self._get_basic_schema_info()
        
        return schema_info
    
    def _get_schema_via_docker(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive schema info via Docker for local Supabase."""
        import subprocess
        
        schema_info = {}
        
        try:
            # Query for table information including comments and row counts
            sql_query = """
            SELECT 
                t.table_name,
                obj_description(c.oid) as table_comment,
                (SELECT count(*) FROM information_schema.tables t2 
                 WHERE t2.table_name = t.table_name AND t2.table_schema = 'public') as exists_check
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name;
            """
            
            result = subprocess.run([
                'docker', 'exec', '-i', 'supabase-db',
                'psql', '-U', 'postgres', '-d', 'postgres', '-t', '-A', '-F|'
            ], input=sql_query, text=True, capture_output=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 2:
                            table_name = parts[0].strip()
                            comment = parts[1].strip() if parts[1].strip() else self._get_default_description(table_name)
                            
                            # Get row count for each table
                            row_count = self._get_table_row_count(table_name)
                            
                            schema_info[table_name] = {
                                'description': comment,
                                'record_count': row_count,
                                'type': 'table'
                            }
                            
        except Exception as e:
            print(f"Error getting schema info via Docker: {e}")
            return self._get_basic_schema_info()
        
        return schema_info
    
    def _get_table_row_count(self, table_name: str) -> str:
        """Get row count for a specific table via Docker."""
        import subprocess
        
        try:
            count_sql = f"SELECT COUNT(*) FROM {table_name};"
            result = subprocess.run([
                'docker', 'exec', '-i', 'supabase-db',
                'psql', '-U', 'postgres', '-d', 'postgres', '-t', '-A'
            ], input=count_sql, text=True, capture_output=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "Error"
                
        except Exception:
            return "Unknown"
    
    def _get_basic_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """Get basic schema info for cloud Supabase (fallback)."""
        # Fallback for cloud - use predefined descriptions
        basic_info = {}
        stats = self.get_stats()
        table_counts = stats.get('tables', {})
        
        for table in self.list_collections():
            basic_info[table] = {
                'description': self._get_default_description(table),
                'record_count': table_counts.get(table, 'Unknown'),
                'type': 'table'
            }
        
        return basic_info
    
    def _get_default_description(self, table_name: str) -> str:
        """Get default description for known tables."""
        descriptions = {
            'sources': 'Source metadata and summaries',
            'crawled_pages': 'Chunked documentation with embeddings (legacy)',
            'code_examples': 'Code snippets with summaries (legacy)',
            'files': 'Individual files with content hashing and metadata',
            'content_chunks': 'File-based text chunks with embeddings (new RAG system)'
        }
        return descriptions.get(table_name, f'Table: {table_name}')
    
    # Document Ingest Interface Implementation
    def check_file_exists(self, file_path: str, content_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file already exists in database with same hash."""
        try:
            result = self._client.table('files').select('*').eq('file_path', file_path).eq('content_hash', content_hash).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None
    
    def remove_file_data(self, file_path: str) -> bool:
        """Remove existing file and its chunks from database."""
        try:
            # Get file record
            file_result = self._client.table('files').select('id').eq('file_path', file_path).execute()
            if file_result.data:
                file_id = file_result.data[0]['id']
                
                # Delete content_chunks first (foreign key constraint)
                self._client.table('content_chunks').delete().eq('file_id', file_id).execute()
                
                # Delete file record
                self._client.table('files').delete().eq('id', file_id).execute()
            return True
        except Exception:
            return False
    
    def store_file_record(self, file_path: str, content_hash: str, file_size: int, content_type: str = 'documentation') -> str:
        """Store file record and return file ID."""
        file_data = {
            'file_path': file_path,
            'content_hash': content_hash,
            'file_size': file_size,
            'content_type': content_type,
            'word_count': 0,
            'chunk_count': 0
        }
        result = self._client.table('files').insert(file_data).execute()
        return result.data[0]['id']
    
    def store_chunks(self, file_id: str, chunks: List[Any], file_path: str) -> Dict[str, int]:
        """Store chunks in database and return statistics."""
        total_chunks = 0
        total_words = 0
        chunk_records = []
        
        for i, chunk in enumerate(chunks):
            # Convert ProcessedChunk to database record
            chunk_data = {
                'file_id': file_id,
                'url': file_path,
                'chunk_number': i,
                'content': chunk.content,
                'content_type': 'documentation',
                'metadata': {
                    'title': chunk.metadata.heading_hierarchy[-1] if chunk.metadata.heading_hierarchy else '',
                    'section': ' > '.join(chunk.metadata.heading_hierarchy),
                    'heading_hierarchy': chunk.metadata.heading_hierarchy,
                    'word_count': chunk.metadata.char_count // 5,  # Rough word count estimate
                    'has_code': chunk.metadata.contains_code,
                    'language_hints': chunk.metadata.code_languages
                },
                'embedding': chunk.embedding if chunk.embedding else None
            }
            
            chunk_records.append(chunk_data)
            total_words += getattr(chunk.metadata, 'word_count', 0)
        
        total_chunks = len(chunk_records)
        
        # Batch insert chunks
        if chunk_records:
            self._client.table('content_chunks').insert(chunk_records).execute()
        
        return {'chunks': total_chunks, 'words': total_words}
    
    def update_file_statistics(self, file_id: str, chunk_count: int, word_count: int) -> bool:
        """Update file record with processing statistics."""
        try:
            self._client.table('files').update({
                'word_count': word_count,
                'chunk_count': chunk_count
            }).eq('id', file_id).execute()
            return True
        except Exception:
            return False