"""
Database management CLI commands.

This module provides commands for database operations including:
- Database information and status
- Data management (deletion, stats)
- Backend configuration
"""

import click
from typing import Optional
from pathlib import Path

from .utils import handle_cli_errors, verbose_echo, format_table_output, confirm_destructive_action

# Import backends with proper path handling
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backends import get_backend


@click.group()
@click.pass_context
def db(ctx):
    """Database management operations."""
    ctx.ensure_object(dict)


@db.command()
@click.pass_context
@handle_cli_errors
def info(ctx):
    """Display database connection and schema information."""
    verbose_echo(ctx, f"Gathering database information for default backend...")
    
    try:
        backend = get_backend()
        stats = backend.get_stats()
        
        click.echo("🗄️ Database Information")
        click.echo("=" * 40)
        
        # Basic info
        click.echo(f"Backend: {backend.get_backend_name()}")
        click.echo(f"Connection: {'✅ Active' if backend.is_connected() else '❌ Failed'}")
        
        # Backend-specific configuration
        config_info = backend.get_config_info()
        format_table_output(config_info, "\n📊 Configuration")
        
        # Data statistics
        if backend.is_connected():
            collections = backend.list_collections()
            click.echo(f"\n📋 Collections/Tables ({len(collections)}):")
            
            if backend.get_backend_name() == 'supabase':
                # Show table info for Supabase
                for table in collections:
                    count = stats.get('tables', {}).get(table, 'Unknown')
                    click.echo(f"  - {table}: {count} records")
                
                click.echo("\n📚 Schema Information:")
                click.echo("  - sources: Source metadata and summaries")
                click.echo("  - crawled_pages: Chunked documentation with embeddings")
                click.echo("  - code_examples: Code snippets with summaries")
            
            elif backend.get_backend_name() == 'chroma':
                # Show collection info for ChromaDB
                for collection in collections:
                    count = stats.get('collections', {}).get(collection, 'Unknown')
                    click.echo(f"  - {collection}: {count} documents")
        
        else:
            click.echo("❌ Cannot retrieve data statistics - connection failed")
    
    except Exception as e:
        click.echo(f"❌ Failed to get database information: {e}", err=True)
        raise


@db.command()
@click.pass_context
@handle_cli_errors
def stats(ctx):
    """Display detailed database statistics."""
    backend_name = ctx.obj.get('db_backend')
    verbose_echo(ctx, f"Gathering detailed statistics for {backend_name or 'default backend'}...")
    
    try:
        backend = get_backend(backend_name)
        stats = backend.get_stats()
        
        click.echo("📊 Database Statistics")
        click.echo("=" * 30)
        
        format_table_output({
            'Backend': stats.get('backend', 'Unknown'),
            'Connected': '✅ Yes' if backend.is_connected() else '❌ No',
            'Collections': len(backend.list_collections()) if backend.is_connected() else 'N/A'
        })
        
        if backend.is_connected():
            if backend.get_backend_name() == 'supabase':
                tables_data = stats.get('tables', {})
                if tables_data:
                    format_table_output(tables_data, "\n📋 Table Record Counts")
            
            elif backend.get_backend_name() == 'chroma':
                collections_data = stats.get('collections', {})
                if collections_data:
                    format_table_output(collections_data, "\n📋 Collection Document Counts")
    
    except Exception as e:
        click.echo(f"❌ Failed to get database statistics: {e}", err=True)
        raise




@db.command()
@click.option('--table', '-t', type=click.Choice(['sources', 'crawled_pages', 'code_examples', 'files', 'content_chunks', 'all']), 
              default='all', help='Specify which table/collection to list')
@click.option('--limit', '-l', type=int, default=10, help='Number of records to display')
@click.pass_context
@handle_cli_errors
def list_all(ctx, table: str, limit: int):
    """List all records from database tables/collections."""
    backend_name = ctx.obj.get('db_backend')
    verbose_echo(ctx, f"Listing records from {table} table(s)...")
    
    try:
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        def list_table_data(table_name: str):
            click.echo(f"\n📋 {table_name.upper()} (showing up to {limit} records)")
            click.echo("-" * 50)
            
            try:
                if backend.get_backend_name() == 'supabase':
                    # Get Supabase client directly for data listing
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))
                    from utils import get_supabase_client
                    
                    client = get_supabase_client()
                    
                    if table_name == 'sources':
                        response = client.table(table_name).select(
                            'source_id,summary,total_word_count,created_at'
                        ).limit(limit).execute()
                        records = response.data if response.data else []
                        
                        for record in records:
                            click.echo(f"  ID: {record['source_id']}")
                            click.echo(f"  Summary: {record.get('summary', 'N/A')[:100]}...")
                            click.echo(f"  Word Count: {record.get('total_word_count', 'N/A')}")
                            click.echo(f"  Created: {record.get('created_at', 'N/A')}")
                            click.echo()
                    
                    elif table_name == 'crawled_pages':
                        response = client.table(table_name).select(
                            'id,url,chunk_number,content,source_id,created_at'
                        ).limit(limit).execute()
                        records = response.data if response.data else []
                        
                        for record in records:
                            click.echo(f"  ID: {record['id']}")
                            click.echo(f"  URL: {record.get('url', 'N/A')}")
                            click.echo(f"  Chunk: {record.get('chunk_number', 'N/A')}")
                            content_preview = record.get('content', 'N/A')[:100] + "..." if record.get('content') else 'N/A'
                            click.echo(f"  Content: {content_preview}")
                            click.echo(f"  Source ID: {record.get('source_id', 'N/A')}")
                            click.echo(f"  Created: {record.get('created_at', 'N/A')}")
                            click.echo()
                    
                    elif table_name == 'code_examples':
                        response = client.table(table_name).select(
                            'id,url,chunk_number,content,summary,source_id,created_at'
                        ).limit(limit).execute()
                        records = response.data if response.data else []
                        
                        for record in records:
                            click.echo(f"  ID: {record['id']}")
                            click.echo(f"  URL: {record.get('url', 'N/A')}")
                            click.echo(f"  Chunk: {record.get('chunk_number', 'N/A')}")
                            content_preview = record.get('content', 'N/A')[:100] + "..." if record.get('content') else 'N/A'
                            click.echo(f"  Content: {content_preview}")
                            summary = record.get('summary', 'N/A')
                            if summary and summary != 'N/A':
                                summary_preview = summary[:100] + "..." if len(summary) > 100 else summary
                            else:
                                summary_preview = 'N/A'
                            click.echo(f"  Summary: {summary_preview}")
                            click.echo(f"  Source ID: {record.get('source_id', 'N/A')}")
                            click.echo(f"  Created: {record.get('created_at', 'N/A')}")
                            click.echo()
                    
                    if not records:
                        click.echo(f"  📭 No records found in {table_name}")
                
                elif backend.get_backend_name() == 'chroma':
                    # For ChromaDB, list collections and their document samples
                    import chromadb
                    chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
                    client = chromadb.PersistentClient(path=chroma_path)
                    
                    if table_name in backend.list_collections():
                        collection = client.get_collection(table_name)
                        result = collection.peek(limit=limit)
                        
                        if result['ids']:
                            for i, doc_id in enumerate(result['ids']):
                                click.echo(f"  ID: {doc_id}")
                                if result['metadatas'] and i < len(result['metadatas']):
                                    metadata = result['metadatas'][i]
                                    for key, value in metadata.items():
                                        click.echo(f"  {key}: {value}")
                                if result['documents'] and i < len(result['documents']):
                                    doc = result['documents'][i]
                                    click.echo(f"  Content: {doc[:100]}...")
                                click.echo()
                        else:
                            click.echo(f"  📭 No documents found in {table_name}")
                    else:
                        click.echo(f"  ❌ Collection {table_name} does not exist")
                        
            except Exception as e:
                click.echo(f"  ❌ Error querying {table_name}: {e}")
        
        if table == 'all':
            collections = backend.list_collections()
            for table_name in collections:
                list_table_data(table_name)
        else:
            list_table_data(table)
        
    except Exception as e:
        click.echo(f"❌ Error listing records: {e}", err=True)
        raise


@db.command()
@click.option('--table', '-t', help='Specific table/collection to delete (if not specified, deletes all)')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
@handle_cli_errors
def delete(ctx, table: Optional[str], force: bool):
    """Delete records from the database."""
    backend_name = ctx.obj.get('db_backend')
    
    # Confirmation check
    if not force:
        target = table if table else "all data"
        if not confirm_destructive_action("delete", target):
            click.echo("❌ Operation cancelled")
            return
    
    verbose_echo(ctx, f"Deleting records from {backend_name or 'default backend'}...")
    
    try:
        backend = get_backend(backend_name)
        
        if table:
            click.echo(f"🗑️ Deleting all records from {table}...")
            success = backend.delete_collection(table)
            if success:
                click.echo(f"✅ Deleted all records from {table}")
            else:
                click.echo(f"❌ Failed to delete records from {table}")
                raise Exception(f"Deletion of {table} failed")
        else:
            click.echo("🗑️ Deleting all records from all collections...")
            success = backend.delete_all_data()
            if success:
                click.echo("✅ Database deletion completed!")
            else:
                click.echo("❌ Some deletions failed")
                raise Exception("Not all data could be deleted")
    
    except Exception as e:
        click.echo(f"❌ Error during deletion: {e}", err=True)
        raise


@db.command()
@click.option('--schema-dir', '-d', type=click.Path(exists=True), 
              default='database/schema', help='Directory containing schema files')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
@handle_cli_errors
def apply_schema(ctx, schema_dir: str, force: bool):
    """Apply database schema files to the current backend."""
    backend_name = ctx.obj.get('db_backend')
    verbose_echo(ctx, f"Applying schema to {backend_name or 'default backend'}...")
    
    try:
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Find schema files
        schema_path = Path(schema_dir)
        sql_files = sorted(schema_path.glob('*.sql'))
        
        if not sql_files:
            click.echo(f"❌ No SQL files found in {schema_dir}", err=True)
            return
        
        # Show files to be applied
        click.echo(f"🗄️ Applying schema to {backend.get_backend_name().upper()}")
        click.echo("=" * 40)
        click.echo(f"Schema directory: {schema_dir}")
        click.echo(f"Files to apply:")
        for sql_file in sql_files:
            click.echo(f"  - {sql_file.name}")
        
        # Confirmation
        if not force:
            if not confirm_destructive_action("apply schema files", f"{len(sql_files)} files"):
                click.echo("❌ Operation cancelled")
                return
        
        # Apply schemas based on backend
        click.echo(f"\n🚀 Applying schema to {backend.get_backend_name()}...")
        
        if backend.get_backend_name() == 'supabase':
            click.echo("📋 Executing SQL files in Supabase...")
            success = backend.apply_schema([str(f) for f in sql_files])
            
        elif backend.get_backend_name() == 'chroma':
            click.echo("📋 Setting up ChromaDB collections...")
            success = backend.apply_schema([str(f) for f in sql_files])
            
        else:
            click.echo(f"❌ Schema application not supported for {backend.get_backend_name()}")
            return
        
        if success:
            click.echo("✅ Schema application completed successfully!")
            click.echo("\n📊 Updated backend information:")
            
            # Show updated stats
            stats = backend.get_stats()
            if backend.get_backend_name() == 'supabase':
                tables = stats.get('tables', {})
                for table, count in tables.items():
                    click.echo(f"  - {table}: {count} records")
            elif backend.get_backend_name() == 'chroma':
                collections = stats.get('collections', {})
                for collection, count in collections.items():
                    click.echo(f"  - {collection}: {count} documents")
        else:
            click.echo("❌ Some schema files failed to apply. Check the output above for details.")
            raise Exception("Schema application failed")
            
    except Exception as e:
        click.echo(f"❌ Error applying schema: {e}", err=True)
        raise


@db.command()
@click.option('--tables', '-t', help='Comma-separated list of tables to drop (if not specified, drops schema tables)')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
@handle_cli_errors
def drop_schema(ctx, tables: Optional[str], force: bool):
    """Drop database schema tables/collections."""
    backend_name = ctx.obj.get('db_backend')
    verbose_echo(ctx, f"Dropping schema from {backend_name or 'default backend'}...")
    
    try:
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Determine tables to drop
        if tables:
            table_list = [t.strip() for t in tables.split(',')]
        else:
            # Default schema tables (in reverse order for dependencies)
            table_list = ['content_chunks', 'files']
        
        # Show tables to be dropped
        click.echo(f"🗄️ Dropping schema from {backend.get_backend_name().upper()}")
        click.echo("=" * 40)
        click.echo(f"Tables/Collections to drop:")
        for table in table_list:
            click.echo(f"  - {table}")
        
        # Confirmation
        if not force:
            click.echo(f"\n⚠️  WARNING: This will permanently delete the schema structure!")
            click.echo(f"⚠️  All data and structure will be lost for these tables.")
            if not confirm_destructive_action("drop schema", f"{len(table_list)} tables"):
                click.echo("❌ Operation cancelled")
                return
        
        # Drop schema
        click.echo(f"\n🗑️ Dropping schema from {backend.get_backend_name()}...")
        
        if backend.get_backend_name() == 'supabase':
            click.echo("📋 Dropping tables from Supabase...")
            success = backend.drop_schema(table_list)
            
        elif backend.get_backend_name() == 'chroma':
            click.echo("📋 Dropping collections from ChromaDB...")
            success = backend.drop_schema(table_list)
            
        else:
            click.echo(f"❌ Schema dropping not supported for {backend.get_backend_name()}")
            return
        
        if success:
            click.echo("✅ Schema dropping completed successfully!")
            click.echo("\n📊 Updated backend information:")
            
            # Show updated stats
            stats = backend.get_stats()
            if backend.get_backend_name() == 'supabase':
                tables = stats.get('tables', {})
                for table, count in tables.items():
                    click.echo(f"  - {table}: {count} records")
            elif backend.get_backend_name() == 'chroma':
                collections = stats.get('collections', {})
                for collection, count in collections.items():
                    click.echo(f"  - {collection}: {count} documents")
        else:
            click.echo("❌ Some tables failed to drop. Check the output above for details.")
            raise Exception("Schema dropping failed")
            
    except Exception as e:
        click.echo(f"❌ Error dropping schema: {e}", err=True)
        raise


@db.command()
@click.pass_context
@handle_cli_errors
def backend(ctx):
    """Show current backend information and configuration guidance."""
    try:
        backend_client = get_backend()
        current_backend = backend_client.get_backend_name()
        
        click.echo("🗄️ Database Backend Information")
        click.echo("=" * 35)
        click.echo(f"Active Backend: {current_backend}")
        click.echo(f"Connection: {'✅ Active' if backend_client.is_connected() else '❌ Failed'}")
        
        # Show basic stats
        if backend_client.is_connected():
            collections = backend_client.list_collections()
            click.echo(f"Collections/Tables: {len(collections)}")
            
            # Show configuration info for current backend
            config_info = backend_client.get_config_info()
            format_table_output(config_info, "\n📊 Current Configuration")
        
        # Show how to change backend
        click.echo("\n⚙️ How to Change Backend:")
        click.echo("  1. Edit .env file:")
        click.echo("     DB_BACKEND=supabase  # For production (PostgreSQL + pgvector)")
        click.echo("     DB_BACKEND=chroma    # For local development")
        click.echo("  2. Restart your application")
        
        click.echo("\n📝 Backend Requirements:")
        click.echo("  Supabase:")
        click.echo("    - SUPABASE_URL=your_project_url")
        click.echo("    - SUPABASE_SERVICE_KEY=your_service_key")
        click.echo("  ChromaDB:")
        click.echo("    - CHROMA_DB_PATH=./chroma_db (optional, default)")
        
    except Exception as e:
        click.echo(f"❌ Error getting backend information: {e}", err=True)
        raise


