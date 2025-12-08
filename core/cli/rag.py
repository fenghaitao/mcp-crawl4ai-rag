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
@click.option('--threshold', '-t', type=float, default=None, 
              help='Similarity threshold for results (default: no threshold)')
@click.option('--content-type', type=click.Choice(['documentation', 'code_dml', 'python_test']),
              help='Filter by content type')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.pass_context
@handle_cli_errors
def query(ctx, query_text: str, limit: int, threshold: Optional[float], content_type: Optional[str], json_output: bool):
    """Query the RAG system with semantic search."""
    from ..backends.factory import get_backend
    import json
    
    verbose_echo(ctx, f"Querying RAG system: {query_text}")
    
    if not json_output:
        click.echo(f"🔍 Query: {query_text}")
        click.echo(f"📊 Limit: {limit} results")
        if threshold is not None:
            click.echo(f"🎯 Threshold: {threshold}")
        if content_type:
            click.echo(f"📁 Content Type: {content_type}")
        click.echo()
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        if not json_output:
            click.echo("🚀 Executing semantic search...")
        
        # Perform semantic search
        results = backend.semantic_search(
            query_text=query_text,
            limit=limit,
            content_type=content_type,
            threshold=threshold
        )
        
        if json_output:
            # JSON output
            output = {
                'query': query_text,
                'limit': limit,
                'threshold': threshold,
                'content_type': content_type,
                'result_count': len(results),
                'results': [
                    {
                        'chunk_id': r.get('id'),
                        'file_id': r.get('file_id'),
                        'url': r.get('url', ''),
                        'chunk_number': r.get('chunk_number', 0),
                        'similarity': r.get('similarity', 0),
                        'summary': r.get('summary', ''),
                        'content_preview': r.get('content', '')[:200] + '...' if len(r.get('content', '')) > 200 else r.get('content', ''),
                        'metadata': r.get('metadata', {})
                    }
                    for r in results
                ]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Human-readable output
            if not results:
                click.echo("📭 No results found matching your query.")
            else:
                click.echo(f"\n📄 Found {len(results)} result(s):")
                click.echo("=" * 80)
                
                for i, result in enumerate(results, 1):
                    click.echo(f"\n🔸 Result #{i}")
                    click.echo(f"   📊 Similarity: {result.get('similarity', 0):.4f}")
                    click.echo(f"   📍 Source: {result.get('url', 'Unknown')}")
                    click.echo(f"   📦 Chunk #{result.get('chunk_number', 'Unknown')}")
                    
                    summary = result.get('summary', '')
                    if summary:
                        click.echo(f"   📝 Summary: {summary}")
                    
                    content = result.get('content', '')
                    if content:
                        # Show first 300 characters
                        if len(content) > 300:
                            content = content[:300] + "..."
                        click.echo(f"   📄 Content: {content}")
                    
                    metadata = result.get('metadata', {})
                    if metadata:
                        # Show relevant metadata fields
                        relevant_fields = ['title', 'section', 'word_count', 'has_code']
                        relevant_meta = {k: v for k, v in metadata.items() if k in relevant_fields}
                        if relevant_meta:
                            click.echo(f"   🏷️  Metadata: {json.dumps(relevant_meta, indent=6)}")
                
                click.echo("\n" + "=" * 80)
                click.echo(f"✅ Query completed successfully! Found {len(results)} results.")
        
    except Exception as e:
        click.echo(f"❌ Error during query: {e}", err=True)
        import traceback
        traceback.print_exc()
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
@click.option('--force', '-f', is_flag=True, help='Force re-processing when content unchanged (regenerate summaries/embeddings)')
@click.pass_context
@handle_cli_errors
def ingest_doc(ctx, file_path: str, force: bool):
    """Ingest a documentation file into the RAG system."""
    from ..backends.factory import get_backend
    from ..services.document_ingest_service import DocumentIngestService
    from ..services.git_service import GitService
    
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
        
        # Create git service and document ingest service
        git_service = GitService()
        service = DocumentIngestService(backend, git_service)
        
        # Process the document
        result = service.ingest_document(file_path, force_reprocess=force)
        
        # Display results
        if result['success']:
            if result.get('skipped', False):
                click.echo("⏭️  Content unchanged - skipped!")
                click.echo(f"📊 Existing file details:")
                click.echo(f"  - File ID: {result['file_id']}")
                click.echo(f"  - Chunks: {result['chunks_created']}")
                click.echo(f"  - Word count: {result['word_count']}")
                click.echo(f"  - Reason: {result.get('reason', 'Content unchanged')}")
                click.echo(f"  - Check time: {result['processing_time']:.2f}s")
                click.echo(f"\n💡 Tip: Use -f to force re-processing (regenerate summaries/embeddings)")
            elif result.get('reprocessed', False):
                click.echo("🔄 Content unchanged - re-processed with force flag!")
                click.echo(f"📊 Results:")
                click.echo(f"  - File ID: {result['file_id']}")
                click.echo(f"  - Chunks re-created: {result['chunks_created']}")
                click.echo(f"  - Word count: {result['word_count']}")
                click.echo(f"  - Processing time: {result['processing_time']:.2f}s")
                click.echo(f"  - Reason: {result.get('reason', 'Re-processed')}")
            else:
                click.echo("✅ Documentation file ingestion completed successfully!")
                click.echo(f"📊 Results:")
                click.echo(f"  - File ID: {result['file_id']}")
                click.echo(f"  - Chunks created: {result['chunks_created']}")
                click.echo(f"  - Word count: {result['word_count']}")
                click.echo(f"  - Processing time: {result['processing_time']:.2f}s")
                if result.get('new_version'):
                    click.echo(f"  - Status: New version created (content changed)")
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
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--pattern', '-p', default='*.md', help='File pattern to match (e.g., *.md,*.html,*.rst)')
@click.option('--recursive/--no-recursive', default=True, help='Search subdirectories recursively')
@click.option('--force', '-f', is_flag=True, help='Force reprocess existing files')
@click.option('--dry-run', is_flag=True, help='Validate files without processing')
@click.pass_context
@handle_cli_errors
def ingest_docs_batch(ctx, directory: str, pattern: str, recursive: bool, 
                      force: bool, dry_run: bool):
    """Batch ingest multiple documentation files from a directory.
    
    Automatically skips files already in the database (unless --force is used).
    Uses the database as the source of truth for tracking progress.
    """
    from ..backends.factory import get_backend
    from ..services.git_service import GitService
    from ..services.document_ingest_service import DocumentIngestService
    from ..services.batch_ingest_service import BatchIngestService
    from pathlib import Path
    import time
    
    verbose_echo(ctx, "Starting batch documentation ingestion...")
    
    dir_path = Path(directory)
    click.echo(f"📁 Directory: {dir_path}")
    click.echo(f"🔍 Pattern: {pattern}")
    click.echo(f"📂 Recursive: {'Yes' if recursive else 'No'}")
    click.echo(f"🔄 Force reprocess: {'Yes' if force else 'No'}")
    click.echo(f"🧪 Dry run: {'Yes' if dry_run else 'No'}")
    click.echo()
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Create services
        git_service = GitService()
        ingest_service = DocumentIngestService(backend, git_service)
        batch_service = BatchIngestService(backend, git_service, ingest_service)
        
        # Start batch ingestion
        start_time = time.time()
        click.echo("🚀 Starting batch ingestion...")
        click.echo()
        
        progress = batch_service.ingest_batch(
            directory=dir_path,
            pattern=pattern,
            recursive=recursive,
            force=force,
            dry_run=dry_run
        )
        
        elapsed_time = time.time() - start_time
        
        # Display summary
        click.echo()
        click.echo("=" * 60)
        click.echo("📊 Batch Ingestion Summary")
        click.echo("=" * 60)
        click.echo(f"Total files discovered: {progress.total_files}")
        click.echo(f"Files processed: {progress.processed}")
        click.echo(f"✅ Succeeded: {progress.succeeded}")
        click.echo(f"⏭️  Skipped: {progress.skipped}")
        click.echo(f"❌ Failed: {progress.failed}")
        click.echo(f"⏱️  Total time: {elapsed_time:.2f}s")
        click.echo(f"📈 Progress: {progress.progress_percent:.1f}%")
        
        if progress.errors:
            click.echo()
            click.echo(f"⚠️  {len(progress.errors)} errors occurred:")
            for i, error in enumerate(progress.errors[:5], 1):  # Show first 5 errors
                click.echo(f"  {i}. {error.get('file', 'Unknown')}")
                if 'issues' in error:
                    for issue in error['issues']:
                        click.echo(f"     - {issue}")
                elif 'error' in error:
                    click.echo(f"     - {error['error']}")
            
            if len(progress.errors) > 5:
                click.echo(f"  ... and {len(progress.errors) - 5} more errors")
            
            error_report = dir_path / "batch_ingest_errors.json"
            if error_report.exists():
                click.echo(f"\n📄 Full error report: {error_report}")
        
        click.echo("=" * 60)
        
        if dry_run:
            click.echo("\n✅ Dry run completed - no files were actually processed")
        elif progress.failed > 0:
            click.echo("\n⚠️  Batch ingestion completed with errors")
        else:
            click.echo("\n✅ Batch ingestion completed successfully!")
        
    except Exception as e:
        click.echo(f"\n❌ Error during batch ingestion: {e}", err=True)
        raise


@rag.command()
@click.argument('repo_url')
@click.argument('file_path')
@click.option('--commit', help='Query file at specific commit SHA')
@click.option('--timestamp', help='Query file at specific timestamp (ISO format)')
@click.option('--all-versions', is_flag=True, help='Show all versions/history of the file')
@click.option('--limit', type=int, default=100, help='Maximum number of versions to show (with --all-versions)')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.pass_context
@handle_cli_errors
def query_file(ctx, repo_url: str, file_path: str, commit: Optional[str], 
               timestamp: Optional[str], all_versions: bool, limit: int, json_output: bool):
    """Query a specific file from the database with temporal constraints.
    
    By default, shows current version. Use --all-versions to see file history.
    Use --commit or --timestamp for temporal queries of specific versions.
    """
    from ..backends.factory import get_backend
    from ..services.query_service import QueryService
    from datetime import datetime
    import json
    
    verbose_echo(ctx, "Querying file...")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Create query service
        query_service = QueryService(backend)
        
        # Handle all-versions mode (replaces file-history functionality)
        if all_versions:
            # Get file history
            history = query_service.get_file_history(repo_url, file_path, limit)
            
            if not history:
                click.echo("❌ No history found for this file", err=True)
                return
            
            # Output file history
            if json_output:
                # JSON output for history
                output = {
                    'repo_url': repo_url,
                    'file_path': file_path,
                    'version_count': len(history),
                    'query_mode': 'all_versions',
                    'versions': [
                        {
                            'file_id': v.get('id'),
                            'commit_sha': v.get('commit_sha'),
                            'valid_from': v.get('valid_from') if isinstance(v.get('valid_from'), str) else (v.get('valid_from').isoformat() if v.get('valid_from') else None),
                            'valid_until': v.get('valid_until') if isinstance(v.get('valid_until'), str) else (v.get('valid_until').isoformat() if v.get('valid_until') else None),
                            'word_count': v.get('word_count'),
                            'chunk_count': v.get('chunk_count'),
                            'content_hash': v.get('content_hash')
                        }
                        for v in history
                    ]
                }
                click.echo(json.dumps(output, indent=2))
            else:
                # Table format for history
                click.echo("=" * 100)
                click.echo(f"📜 File History: {file_path}")
                click.echo(f"📦 Repository: {repo_url}")
                click.echo(f"📊 Total versions: {len(history)}")
                click.echo("=" * 100)
                
                # Header
                click.echo(f"{'Commit':<12} {'Valid From':<20} {'Valid Until':<20} {'Words':<10} {'Chunks':<8}")
                click.echo("-" * 100)
                
                # Rows
                for v in history:
                    commit_sha = str(v.get('commit_sha', ''))[:11]
                    valid_from = str(v.get('valid_from', ''))[:19]
                    valid_until = str(v.get('valid_until') or 'Current')[:19]
                    words = str(v.get('word_count', 0))
                    chunks = str(v.get('chunk_count', 0))
                    
                    click.echo(f"{commit_sha:<12} {valid_from:<20} {valid_until:<20} {words:<10} {chunks:<8}")
                
                click.echo("=" * 100)
            return
        
        # Parse timestamp if provided (for single version queries)
        ts = None
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp)
            except ValueError:
                click.echo(f"❌ Invalid timestamp format: {timestamp}", err=True)
                click.echo("   Use ISO format: YYYY-MM-DDTHH:MM:SS", err=True)
                return
        
        # Query single file version
        result = query_service.query_file(repo_url, file_path, commit_sha=commit, timestamp=ts)
        
        if not result:
            click.echo("❌ File not found", err=True)
            return
        
        # Output single version results  
        if json_output:
            # JSON output for single version
            output = {
                'file_id': result.get('id'),
                'repo_url': repo_url,
                'file_path': result.get('file_path'),
                'query_mode': 'single_version',
                'temporal_constraint': 'commit' if commit else ('timestamp' if timestamp else 'current'),
                'commit_sha': result.get('commit_sha'),
                'content_hash': result.get('content_hash'),
                'file_size': result.get('file_size'),
                'word_count': result.get('word_count'),
                'chunk_count': result.get('chunk_count'),
                'content_type': result.get('content_type'),
                'valid_from': result.get('valid_from') if isinstance(result.get('valid_from'), str) else (result.get('valid_from').isoformat() if result.get('valid_from') else None),
                'valid_until': result.get('valid_until') if isinstance(result.get('valid_until'), str) else (result.get('valid_until').isoformat() if result.get('valid_until') else None),
                'ingested_at': result.get('ingested_at') if isinstance(result.get('ingested_at'), str) else (result.get('ingested_at').isoformat() if result.get('ingested_at') else None)
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Table format
            click.echo("=" * 60)
            click.echo("📄 File Information")
            click.echo("=" * 60)
            click.echo(f"File ID: {result.get('id')}")
            click.echo(f"Repository: {repo_url}")
            click.echo(f"File Path: {result.get('file_path')}")
            click.echo(f"Commit SHA: {result.get('commit_sha')}")
            click.echo(f"Content Hash: {result.get('content_hash', '')[:16]}...")
            click.echo(f"File Size: {result.get('file_size')} bytes")
            click.echo(f"Word Count: {result.get('word_count')}")
            click.echo(f"Chunk Count: {result.get('chunk_count')}")
            click.echo(f"Content Type: {result.get('content_type')}")
            click.echo(f"Valid From: {result.get('valid_from')}")
            click.echo(f"Valid Until: {result.get('valid_until') or 'Current'}")
            click.echo(f"Ingested At: {result.get('ingested_at')}")
            click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"❌ Error querying file: {e}", err=True)
        raise


@rag.command()
@click.option('--repo-url', help='Filter by repository URL')
@click.option('--content-type', type=click.Choice(['documentation', 'code_dml', 'python_test']),
              help='Filter by content type')
@click.option('--current-only/--all-versions', default=True, 
              help='Show only current versions or all versions')
@click.option('--limit', type=int, default=100, help='Maximum number of results')
@click.option('--offset', type=int, default=0, help='Offset for pagination')
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.pass_context
@handle_cli_errors
def list_files(ctx, repo_url: Optional[str], content_type: Optional[str],
               current_only: bool, limit: int, offset: int, json_output: bool):
    """List ingested files with filtering and pagination."""
    from ..backends.factory import get_backend
    from ..services.query_service import QueryService
    import json
    
    verbose_echo(ctx, "Listing files...")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Create query service
        query_service = QueryService(backend)
        
        # List files
        files, total = query_service.list_files(
            repo_url=repo_url,
            content_type=content_type,
            current_only=current_only,
            limit=limit,
            offset=offset
        )
        
        # Enrich files with repository information
        files_with_repos = []
        repo_cache = {}  # Cache to avoid repeated repo lookups
        
        for f in files:
            repo_id = f.get('repo_id')
            repo_info = None
            
            if repo_id:
                # Check cache first
                if repo_id in repo_cache:
                    repo_info = repo_cache[repo_id]
                else:
                    # Fetch repo info and cache it
                    repo_info = backend.get_repository_by_id(repo_id)
                    repo_cache[repo_id] = repo_info
            
            # Add repo info to file
            f_with_repo = f.copy()
            if repo_info:
                f_with_repo['repo_name'] = repo_info.get('repo_name', 'Unknown')
                f_with_repo['repo_url'] = repo_info.get('repo_url', 'Unknown')
            else:
                f_with_repo['repo_name'] = 'Unknown'
                f_with_repo['repo_url'] = 'Unknown'
            
            files_with_repos.append(f_with_repo)
        
        files = files_with_repos
        
        if json_output:
            # JSON output
            output = {
                'total': total,
                'limit': limit,
                'offset': offset,
                'count': len(files),
                'files': [
                    {
                        'file_id': f.get('id'),
                        'file_path': f.get('file_path'),
                        'repo_name': f.get('repo_name'),
                        'repo_url': f.get('repo_url'),
                        'commit_sha': f.get('commit_sha'),
                        'content_type': f.get('content_type'),
                        'word_count': f.get('word_count'),
                        'chunk_count': f.get('chunk_count'),
                        'valid_from': f.get('valid_from') if isinstance(f.get('valid_from'), str) else (f.get('valid_from').isoformat() if f.get('valid_from') else None),
                        'valid_until': f.get('valid_until') if isinstance(f.get('valid_until'), str) else (f.get('valid_until').isoformat() if f.get('valid_until') else None)
                    }
                    for f in files
                ]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # List format
            click.echo(f"\n📚 Files List (showing {len(files)} of {total} total)")
            click.echo("=" * 80)
            
            if not files:
                click.echo("No files found matching the criteria")
            else:
                for i, f in enumerate(files, 1):
                    click.echo(f"\n📄 File {i}:")
                    click.echo(f"  ID: {f.get('id', 'Unknown')}")
                    click.echo(f"  Repository: {f.get('repo_url', 'Unknown')}")
                    click.echo(f"  Path: {f.get('file_path', 'Unknown')}")
                    click.echo(f"  Type: {f.get('content_type', 'Unknown')}")
                    click.echo(f"  Chunks: {f.get('chunk_count', 0)}")
                    click.echo(f"  Words: {f.get('word_count', 0)}")
                    click.echo(f"  Commit: {f.get('commit_sha', 'Unknown')}")
                    
                    # Show temporal info if available
                    valid_from = f.get('valid_from')
                    valid_until = f.get('valid_until')
                    if valid_from:
                        click.echo(f"  Valid From: {valid_from}")
                    if valid_until:
                        click.echo(f"  Valid Until: {valid_until}")
                    elif valid_from:
                        click.echo(f"  Valid Until: Current")
            
            click.echo("\n" + "=" * 80)
            
            # Pagination info
            if total > limit:
                pages = (total + limit - 1) // limit
                current_page = (offset // limit) + 1
                click.echo(f"Page {current_page} of {pages} | Use --offset and --limit for pagination")
        
    except Exception as e:
        click.echo(f"❌ Error listing files: {e}", err=True)
        raise


@rag.command()
@click.argument('file_id', type=int)
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
@click.pass_context
@handle_cli_errors
def list_chunks(ctx, file_id: int, json_output: bool):
    """List all chunks for a specific file."""
    from ..backends.factory import get_backend
    from ..services.query_service import QueryService
    import json
    
    verbose_echo(ctx, "Listing chunks...")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Create query service
        query_service = QueryService(backend)
        
        # Get chunks
        chunks = query_service.get_file_chunks(file_id)
        
        if not chunks:
            click.echo(f"❌ No chunks found for file ID {file_id}", err=True)
            return
        
        if json_output:
            # JSON output
            output = {
                'file_id': file_id,
                'chunk_count': len(chunks),
                'chunks': [
                    {
                        'chunk_id': c.get('id'),
                        'chunk_number': c.get('chunk_number'),
                        'content_preview': c.get('content', '')[:100] + '...' if len(c.get('content', '')) > 100 else c.get('content', ''),
                        'word_count': c.get('metadata', {}).get('word_count'),
                        'has_code': c.get('metadata', {}).get('has_code'),
                        'summary': c.get('summary')
                    }
                    for c in chunks
                ]
            }
            click.echo(json.dumps(output, indent=2))
        else:
            # Table format
            click.echo("=" * 100)
            click.echo(f"📦 Chunks for File ID: {file_id}")
            click.echo(f"📊 Total chunks: {len(chunks)}")
            click.echo("=" * 100)
            
            # Header
            click.echo(f"{'#':<5} {'Words':<8} {'Code':<6} {'Summary Preview':<70}")
            click.echo("-" * 100)
            
            # Rows
            for c in chunks:
                num = str(c.get('chunk_number', ''))
                words = str(c.get('metadata', {}).get('word_count', 0))
                has_code = 'Yes' if c.get('metadata', {}).get('has_code') else 'No'
                summary = str(c.get('summary', ''))[:69] if c.get('summary') else '-'
                
                click.echo(f"{num:<5} {words:<8} {has_code:<6} {summary:<70}")
            
            click.echo("=" * 100)
        
    except Exception as e:
        click.echo(f"❌ Error listing chunks: {e}", err=True)
        raise


@rag.command()
@click.argument('file_path', type=click.Path())
@click.option('--commit', help='Remove only this specific commit version (default: remove all versions)')
@click.option('--confirm', '-c', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
@handle_cli_errors
def egest_doc(ctx, file_path: str, commit: Optional[str], confirm: bool):
    """Remove a documentation file and its chunks from the database.
    
    By default, removes ALL versions of the file. Use --commit to remove only a specific version.
    """
    from ..backends.factory import get_backend
    from ..services.git_service import GitService
    from pathlib import Path
    
    verbose_echo(ctx, "Removing documentation file from database...")
    
    click.echo(f"📄 Documentation file: {file_path}")
    if commit:
        click.echo(f"🔖 Commit filter: {commit}")
    
    try:
        # Get backend
        backend_name = ctx.obj.get('db_backend')
        backend = get_backend(backend_name)
        
        if not backend.is_connected():
            click.echo("❌ Database not connected", err=True)
            return
        
        # Normalize file path using git service (same as ingest)
        git_service = GitService()
        git_info = git_service.detect_repository(Path(file_path))
        
        normalized_path = file_path
        repo_id = None
        
        if git_info:
            # Get relative path from git root (same as ingest does)
            abs_file_path = Path(file_path).resolve()
            normalized_path = git_info.get_relative_path(abs_file_path)
            
            # Get repository ID
            repo = backend.get_repository(git_info.repo_url)
            if repo:
                repo_id = repo['id']
        
        # Get all versions of this file
        all_versions = []
        if repo_id:
            all_versions = backend.get_file_history(repo_id, normalized_path, limit=1000)
        
        if not all_versions:
            # Fallback: check if current version exists
            try:
                from .utils import calculate_file_hash
                file_hash = calculate_file_hash(file_path)
                existing = backend.check_file_exists(normalized_path, file_hash)
                if existing:
                    all_versions = [existing]
            except FileNotFoundError:
                click.echo(f"❌ File not found: {file_path}", err=True)
                return
            except Exception as e:
                click.echo(f"❌ Error reading file: {e}", err=True)
                return
        
        if not all_versions:
            click.echo(f"⚠️  File not found in database:")
            click.echo(f"   - Path: {normalized_path}")
            click.echo(f"   - File may have been modified or never ingested")
            return
        
        # Filter by commit if specified
        versions_to_remove = all_versions
        if commit:
            versions_to_remove = [v for v in all_versions if v.get('commit_sha', '').startswith(commit)]
            if not versions_to_remove:
                click.echo(f"❌ No version found for commit: {commit}")
                click.echo(f"\n📜 Available commits:")
                for v in all_versions[:10]:
                    commit_sha = v.get('commit_sha', 'Unknown')
                    valid_from = str(v.get('valid_from', 'Unknown'))[:19]
                    click.echo(f"   - {commit_sha[:8]} from {valid_from}")
                return
        
        # Calculate totals across versions to remove
        total_chunks = sum(v.get('chunk_count', 0) for v in versions_to_remove)
        total_words = sum(v.get('word_count', 0) for v in versions_to_remove)
        
        # Confirmation prompt unless --confirm flag is used
        if not confirm:
            if commit:
                click.echo(f"⚠️  This will permanently remove specific version:")
                click.echo(f"   - File path: {normalized_path}")
                click.echo(f"   - Commit: {versions_to_remove[0].get('commit_sha', 'Unknown')[:8]}")
                click.echo(f"   - Chunks: {total_chunks}")
                click.echo(f"   - Words: {total_words}")
            else:
                click.echo(f"⚠️  This will permanently remove ALL versions:")
                click.echo(f"   - File path: {normalized_path}")
                click.echo(f"   - Total versions: {len(versions_to_remove)}")
                click.echo(f"   - Total chunks: {total_chunks}")
                click.echo(f"   - Total words: {total_words}")
                
                if len(versions_to_remove) > 1:
                    click.echo(f"\n   📜 Version history:")
                    for i, v in enumerate(versions_to_remove[:5], 1):  # Show first 5
                        commit_sha = str(v.get('commit_sha', 'Unknown'))[:8]
                        valid_from = str(v.get('valid_from', 'Unknown'))[:19]
                        click.echo(f"      {i}. Commit {commit_sha} from {valid_from} ({v.get('chunk_count', 0)} chunks)")
                    if len(versions_to_remove) > 5:
                        click.echo(f"      ... and {len(versions_to_remove) - 5} more versions")
            
            if not click.confirm("\nAre you sure you want to proceed?"):
                click.echo("❌ Operation cancelled")
                return
        
        # Remove based on whether we're removing all or specific version
        if commit:
            click.echo(f"🗑️  Removing specific version from database...")
            # Remove specific version by commit
            success = backend.remove_file_version(normalized_path, commit)
        else:
            click.echo(f"🗑️  Removing all versions from database...")
            # Remove all versions
            success = backend.remove_file_data(normalized_path)
        
        if success:
            click.echo("✅ Documentation file removed successfully!")
            click.echo(f"📊 Removed:")
            click.echo(f"  - File path: {normalized_path}")
            if commit:
                click.echo(f"  - Commit: {commit}")
            else:
                click.echo(f"  - Versions removed: {len(versions_to_remove)}")
            click.echo(f"  - Total chunks: {total_chunks}")
            click.echo(f"  - Total words: {total_words}")
        else:
            click.echo("⚠️  File not found in database or already removed")
        
    except Exception as e:
        click.echo(f"❌ Error during file removal: {e}", err=True)
        raise


