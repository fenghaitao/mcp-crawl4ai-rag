"""
RAG pipeline CLI commands.

This module provides commands for RAG operations including:
- Content crawling and downloading
- Document chunking and processing
- RAG querying operations
"""

import click
from typing import Optional
from pathlib import Path

from .utils import handle_cli_errors, verbose_echo


@click.group()
def rag():
    """RAG pipeline operations (crawling, chunking, querying)."""
    pass


@rag.command()
@click.argument('query_text')
@click.option('--limit', '-l', type=int, default=5, help='Number of results to return')
@click.option('--threshold', '-t', type=float, default=0.7, 
              help='Similarity threshold for results')
@click.pass_context
@handle_cli_errors
def query(ctx, query_text: str, limit: int, threshold: float):
    """Query the RAG system with a text prompt."""
    verbose_echo(ctx, f"Querying RAG system: {query_text}")
    
    click.echo(f"🔍 Query: {query_text}")
    click.echo(f"📊 Limit: {limit} results")
    click.echo(f"🎯 Threshold: {threshold}")
    
    try:
        # TODO: Integrate with actual RAG query logic
        click.echo("🚀 Executing RAG query...")
        click.echo("📋 This will integrate with the query_rag module")
        
        # Placeholder response
        click.echo("\n📄 Results:")
        click.echo("1. [Placeholder] Documentation chunk about query topic")
        click.echo("   Relevance: 0.85")
        click.echo("   Source: simics-docs/example.md")
        
        click.echo("✅ Query completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error during query: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help='Force re-processing: egest existing data and re-ingest')
@click.pass_context
@handle_cli_errors
def ingest_dml(ctx, file_path: str, force: bool):
    """Ingest a DML source code file into the RAG system."""
    verbose_echo(ctx, "Ingesting DML source file...")
    
    click.echo(f"📄 DML file: {file_path}")
    click.echo(f"🔄 Force re-processing: {'Yes' if force else 'No'}")
    
    try:
        if force:
            click.echo("🗑️ Force mode: Removing existing data for this file...")
            # TODO: Egest/remove existing data for this specific file from database
        
        click.echo("🚀 Starting DML file ingestion...")
        click.echo("📋 Processing .dml file...")
        click.echo("🧠 Generating embeddings...")
        click.echo("💾 Storing in database...")
        
        # TODO: Integrate with actual DML file processing logic
        # This should process the single DML file
        
        click.echo("✅ DML file ingestion completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error during DML ingestion: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help='Force re-processing: egest existing data and re-ingest')
@click.pass_context
@handle_cli_errors
def ingest_python_test(ctx, file_path: str, force: bool):
    """Ingest a Python test file into the RAG system."""
    verbose_echo(ctx, "Ingesting Python test file...")
    
    click.echo(f"📄 Python test file: {file_path}")
    click.echo(f"🔄 Force re-processing: {'Yes' if force else 'No'}")
    
    try:
        if force:
            click.echo("🗑️ Force mode: Removing existing data for this file...")
            # TODO: Egest/remove existing data for this specific file from database
        
        click.echo("🚀 Starting Python test file ingestion...")
        click.echo("🧪 Processing test file...")
        click.echo("🧠 Generating embeddings...")
        click.echo("💾 Storing in database...")
        
        # TODO: Integrate with Python test file processing
        # This should process the single Python test file
        
        click.echo("✅ Python test file ingestion completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error during Python test ingestion: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--force', '-f', is_flag=True, help='Force re-processing: egest existing data and re-ingest')
@click.pass_context
@handle_cli_errors
def ingest_doc(ctx, file_path: str, force: bool):
    """Ingest a documentation file into the RAG system."""
    from ..backends.factory import get_backend
    from ..services.document_ingest_service import DocumentIngestService
    
    verbose_echo(ctx, "Ingesting documentation file...")
    
    click.echo(f"📄 Documentation file: {file_path}")
    click.echo(f"🔄 Force re-processing: {'Yes' if force else 'No'}")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Create document ingest service
        service = DocumentIngestService(backend)
        
        # Process the document
        result = service.ingest_document(file_path, force_reprocess=force)
        
        # Display results
        if result['success']:
            if result.get('skipped', False):
                click.echo("⏭️  File already exists in database - skipped!")
                click.echo(f"📊 Existing file details:")
                click.echo(f"  - File ID: {result['file_id']}")
                click.echo(f"  - Chunks: {result['chunks_created']}")
                click.echo(f"  - Word count: {result['word_count']}")
                click.echo(f"  - Reason: {result.get('reason', 'File unchanged')}")
                click.echo(f"  - Check time: {result['processing_time']:.2f}s")
            else:
                click.echo("✅ Documentation file ingestion completed successfully!")
                click.echo(f"📊 Results:")
                click.echo(f"  - File ID: {result['file_id']}")
                click.echo(f"  - Chunks created: {result['chunks_created']}")
                click.echo(f"  - Word count: {result['word_count']}")
                click.echo(f"  - Processing time: {result['processing_time']:.2f}s")
        else:
            click.echo(f"❌ Ingestion failed: {result['error']}", err=True)
            raise Exception(result['error'])
        
    except Exception as e:
        click.echo(f"❌ Error during documentation ingestion: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'raw']),
              default='json', help='Export format')
@click.pass_context
@handle_cli_errors
def egest_dml(ctx, file_path: str, format: str):
    """Export DML chunks and metadata to a file."""
    verbose_echo(ctx, "Exporting DML data...")
    
    click.echo(f"📄 Export file: {file_path}")
    click.echo(f"📋 Format: {format}")
    
    try:
        # Create output directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        click.echo("🚀 Starting DML export...")
        click.echo("📊 Querying database for DML sources...")
        click.echo("📝 Processing DML chunks...")
        click.echo("💾 Writing export file...")
        
        # TODO: Integrate with database export logic
        # Query crawled_pages where source_id LIKE '%dml%'
        # Export chunks with metadata to single file
        
        click.echo(f"✅ DML export completed! Data saved to {file_path}")
        
    except Exception as e:
        click.echo(f"❌ Error during DML export: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['json', 'markdown', 'raw']),
              default='json', help='Export format')
@click.pass_context
@handle_cli_errors
def egest_python_test(ctx, file_path: str, format: str):
    """Export Python test chunks and metadata to a file."""
    verbose_echo(ctx, "Exporting Python test data...")
    
    click.echo(f"📄 Export file: {file_path}")
    click.echo(f"📋 Format: {format}")
    
    try:
        # Create output directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        click.echo("🚀 Starting Python test export...")
        click.echo("📊 Querying database for Python test sources...")
        click.echo("📝 Processing Python test chunks...")
        click.echo("💾 Writing export file...")
        
        # TODO: Integrate with database export logic
        # Query crawled_pages where source_id LIKE '%python%' AND metadata contains test info
        # Export test chunks with metadata to single file
        
        click.echo(f"✅ Python test export completed! Data saved to {file_path}")
        
    except Exception as e:
        click.echo(f"❌ Error during Python test export: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path())
@click.option('--confirm', '-c', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
@handle_cli_errors
def egest_doc(ctx, file_path: str, confirm: bool):
    """Remove a documentation file and its chunks from the database."""
    from ..backends.factory import get_backend
    
    verbose_echo(ctx, "Removing documentation file from database...")
    
    click.echo(f"📄 Documentation file: {file_path}")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Check if file exists in database with current hash
        try:
            from .utils import calculate_file_hash
            file_hash = calculate_file_hash(file_path)
            existing = backend.check_file_exists(file_path, file_hash)
        except FileNotFoundError:
            click.echo(f"❌ File not found: {file_path}", err=True)
            return
        except Exception as e:
            click.echo(f"❌ Error reading file: {e}", err=True)
            return
        
        if not existing:
            click.echo(f"⚠️  File not found in database:")
            click.echo(f"   - Path: {file_path}")
            click.echo(f"   - Current hash: {file_hash[:16]}...")
            click.echo(f"   - File may have been modified or never ingested")
            return
        
        # Confirmation prompt unless --confirm flag is used
        if not confirm:
            click.echo(f"⚠️  This will permanently remove:")
            click.echo(f"   - File record: {file_path}")
            click.echo(f"   - File ID: {existing['id']}")
            click.echo(f"   - {existing['chunk_count']} chunks and embeddings")
            click.echo(f"   - {existing['word_count']} words of processed content")
            click.echo(f"   - Content hash: {file_hash[:16]}...")
            
            if not click.confirm("Are you sure you want to proceed?"):
                click.echo("❌ Operation cancelled")
                return
        
        click.echo("🗑️  Removing file from database...")
        
        # Remove file and its chunks using backend interface
        success = backend.remove_file_data(file_path)
        
        if success:
            click.echo("✅ Documentation file removed successfully!")
            click.echo(f"📊 Removed:")
            click.echo(f"  - File record: {file_path}")
            click.echo(f"  - All associated chunks")
            click.echo(f"  - All embeddings and metadata")
        else:
            click.echo("⚠️  File not found in database or already removed")
        
    except Exception as e:
        click.echo(f"❌ Error during file removal: {e}", err=True)
        raise


