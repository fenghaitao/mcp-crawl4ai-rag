"""
Supabase database backend implementation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

from .base import DatabaseBackend


class SupabaseBackend(DatabaseBackend):
    """Supabase database backend implementation."""
    
    def __init__(self):
        self._client = None
        self._pg_client = None  # Direct PostgreSQL client for transactions
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
                ('repositories', 'id'),             # Add repositories table
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
        return ['sources', 'crawled_pages', 'code_examples', 'repositories', 'files', 'content_chunks']
    
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
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Note: Supabase Python client doesn't directly support transactions.
        For now, this is a compatibility layer. True transaction support
        would require using psycopg2 directly with the connection string.
        
        TODO: Implement proper PostgreSQL transactions using psycopg2
        """
        try:
            yield self
        except Exception as e:
            # Log the error
            import logging
            logging.getLogger(__name__).error(f"Transaction failed: {e}")
            # In a real implementation, we would rollback here
            raise
    
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
            'repositories': 'Git repositories containing documentation and source code',
            'files': 'File versions with temporal validity tracking',
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
        """Remove existing file and its chunks from database.
        
        Removes ALL versions of the file matching the given path.
        """
        try:
            # Get all file records matching this path
            file_result = self._client.table('files').select('id').eq('file_path', file_path).execute()
            if file_result.data:
                # Delete chunks for all file versions (foreign key constraint)
                for file_record in file_result.data:
                    file_id = file_record['id']
                    self._client.table('content_chunks').delete().eq('file_id', file_id).execute()
                
                # Delete all file records matching this path
                self._client.table('files').delete().eq('file_path', file_path).execute()
            return True
        except Exception:
            return False
    
    def remove_file_version(self, file_path: str, commit_sha: str) -> bool:
        """Remove a specific version of a file by commit SHA.
        
        Args:
            file_path: Path to the file
            commit_sha: Full or partial commit SHA (will match prefix)
        """
        try:
            # Get file records matching path and commit
            file_result = (
                self._client.table('files')
                .select('id, commit_sha')
                .eq('file_path', file_path)
                .execute()
            )
            
            if not file_result.data:
                return False
            
            # Find matching commit(s)
            matching_ids = [
                f['id'] for f in file_result.data 
                if f['commit_sha'].startswith(commit_sha)
            ]
            
            if not matching_ids:
                return False
            
            # Delete chunks for matching versions
            for file_id in matching_ids:
                self._client.table('content_chunks').delete().eq('file_id', file_id).execute()
            
            # Delete matching file records
            for file_id in matching_ids:
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
            word_count = chunk.metadata.char_count // 5  # Rough word count estimate
            chunk_data = {
                'file_id': file_id,
                'url': file_path,
                'chunk_number': i,
                'content': chunk.content,
                'content_type': 'documentation',
                'summary': chunk.summary if chunk.summary else None,
                'metadata': {
                    'title': chunk.metadata.heading_hierarchy[-1] if chunk.metadata.heading_hierarchy else '',
                    'section': ' > '.join(chunk.metadata.heading_hierarchy),
                    'word_count': word_count,
                    'has_code': chunk.metadata.contains_code,
                    'heading_hierarchy': chunk.metadata.heading_hierarchy,  # Keep as list for Supabase JSONB
                    'language_hints': chunk.metadata.code_languages if chunk.metadata.code_languages else []  # Keep as list for Supabase JSONB
                },
                'embedding': chunk.embedding if chunk.embedding else None
            }
            
            chunk_records.append(chunk_data)
            total_words += word_count
        
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

    # Repository operations implementation
    def store_repository(self, repo_url: str, repo_name: str) -> int:
        """Store repository record and return repo_id."""
        try:
            # Use INSERT ON CONFLICT to handle duplicates
            result = self._client.table('repositories').upsert({
                'repo_url': repo_url,
                'repo_name': repo_name,
                'last_ingested_at': 'NOW()'
            }, on_conflict='repo_url').execute()
            
            return result.data[0]['id']
        except Exception as e:
            raise Exception(f"Failed to store repository: {e}")
    
    def get_repository(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Get repository by URL."""
        try:
            result = self._client.table('repositories').select('*').eq('repo_url', repo_url).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None
    
    def get_repository_by_id(self, repo_id: int) -> Optional[Dict[str, Any]]:
        """Get repository by ID."""
        try:
            result = self._client.table('repositories').select('*').eq('id', repo_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None
    
    def update_repository_last_ingested(self, repo_id: int) -> bool:
        """Update last_ingested_at timestamp."""
        try:
            self._client.table('repositories').update({
                'last_ingested_at': 'NOW()'
            }).eq('id', repo_id).execute()
            return True
        except Exception:
            return False

    # Temporal file operations implementation
    def store_file_version(self, file_version: Dict[str, Any]) -> int:
        """Store new file version and update previous version's valid_until."""
        try:
            # First, update any existing current version to set valid_until
            if 'valid_from' in file_version:
                self._client.table('files').update({
                    'valid_until': file_version['valid_from']
                }).eq('repo_id', file_version['repo_id']).eq('file_path', file_version['file_path']).is_('valid_until', 'null').execute()
            
            # Insert new version
            result = self._client.table('files').insert(file_version).execute()
            return result.data[0]['id']
        except Exception as e:
            raise Exception(f"Failed to store file version: {e}")
    
    def get_current_file(self, repo_id: int, file_path: str) -> Optional[Dict[str, Any]]:
        """Get currently valid version of a file (valid_until IS NULL)."""
        try:
            result = self._client.table('files').select('*').eq('repo_id', repo_id).eq('file_path', file_path).is_('valid_until', 'null').execute()
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None
    
    def get_file_at_time(self, repo_id: int, file_path: str, timestamp: Any) -> Optional[Dict[str, Any]]:
        """Get file version valid at specific timestamp."""
        try:
            # Query for file where valid_from <= timestamp AND (valid_until IS NULL OR valid_until > timestamp)
            result = self._client.table('files').select('*').eq('repo_id', repo_id).eq('file_path', file_path).lte('valid_from', timestamp.isoformat()).order('valid_from', desc=True).limit(1).execute()
            
            if result.data:
                file_record = result.data[0]
                # Check valid_until constraint
                if file_record['valid_until'] is None or file_record['valid_until'] > timestamp.isoformat():
                    return file_record
            return None
        except Exception:
            return None
    
    def get_file_at_commit(self, repo_id: int, file_path: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """Get file version from specific commit."""
        try:
            result = self._client.table('files').select('*').eq('repo_id', repo_id).eq('file_path', file_path).eq('commit_sha', commit_sha).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception:
            return None
    
    def get_file_history(self, repo_id: int, file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all versions of a file ordered by valid_from."""
        try:
            result = self._client.table('files').select('*').eq('repo_id', repo_id).eq('file_path', file_path).order('valid_from', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception:
            return []
    
    def list_files(self, repo_id: Optional[int] = None, content_type: Optional[str] = None,
                   current_only: bool = True, limit: int = 100, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """List files with filtering and pagination."""
        try:
            query = self._client.table('files').select('*', count='exact')
            
            # Apply filters
            if repo_id is not None:
                query = query.eq('repo_id', repo_id)
            if content_type is not None:
                query = query.eq('content_type', content_type)
            if current_only:
                query = query.is_('valid_until', 'null')
            
            # Apply pagination and ordering
            result = query.order('ingested_at', desc=True).range(offset, offset + limit - 1).execute()
            
            files = result.data if result.data else []
            total_count = result.count if hasattr(result, 'count') else len(files)
            
            return files, total_count
        except Exception:
            return [], 0
    
    def get_chunks_by_file_id(self, file_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a specific file ID ordered by chunk_number."""
        try:
            result = self._client.table('content_chunks').select('*').eq('file_id', file_id).order('chunk_number').execute()
            return result.data if result.data else []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting chunks for file ID {file_id}: {e}")
            return []
    
    def semantic_search(self, query_text: str, limit: int = 5,
                       content_type: Optional[str] = None,
                       threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Perform semantic search on content chunks using embeddings."""
        import logging
        import sys
        import os
        logger = logging.getLogger(__name__)
        
        try:
            # Generate embedding for the query using the same embedding generator
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))
            from utils import create_embedding
            
            query_embedding = create_embedding(query_text)
            
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Convert numpy array to list if needed
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # Use Supabase's vector similarity search with RPC function
            # The match_documents function should be defined in Supabase
            rpc_params = {
                'query_embedding': query_embedding,
                'match_count': limit
            }
            
            # Add content_type filter if specified
            if content_type:
                rpc_params['filter_content_type'] = content_type
            
            # Try to use the RPC function for vector search
            try:
                result = self._client.rpc('match_content_chunks', rpc_params).execute()
                search_results = result.data if result.data else []
            except Exception as rpc_error:
                logger.warning(f"RPC function not available, falling back to client-side search: {rpc_error}")
                # Fallback: fetch chunks and compute similarity client-side
                query = self._client.table('content_chunks').select('*')
                if content_type:
                    query = query.eq('content_type', content_type)
                result = query.limit(1000).execute()  # Limit to prevent memory issues
                
                if not result.data:
                    return []
                
                # Compute cosine similarity client-side
                import numpy as np
                query_vec = np.array(query_embedding)
                
                search_results = []
                for chunk in result.data:
                    if chunk.get('embedding'):
                        chunk_vec = np.array(chunk['embedding'])
                        # Cosine similarity
                        similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))
                        
                        # Apply threshold filter if specified
                        if threshold is not None and similarity < threshold:
                            continue
                        
                        chunk['similarity'] = float(similarity)
                        search_results.append(chunk)
                
                # Sort by similarity and take top results
                search_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                search_results = search_results[:limit]
            
            # Normalize result format
            for result in search_results:
                # Ensure common fields are accessible
                if 'metadata' in result and isinstance(result['metadata'], dict):
                    result['url'] = result.get('url', result['metadata'].get('url', ''))
                    result['summary'] = result.get('summary', result['metadata'].get('summary', ''))
            
            logger.info(f"Semantic search found {len(search_results)} results for query: {query_text[:50]}...")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            import traceback
            traceback.print_exc()
            return []
