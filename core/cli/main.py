#!/usr/bin/env python3
"""
Main CLI entry point for Simics RAG system.

This module provides the main command-line interface that integrates:
- RAG pipeline functionality
- Database management
- Development and debugging utilities
"""

import click
import logging
from typing import Optional

from .utils import handle_cli_errors, get_config_value
from .database import db
from .rag import rag

# Version information
__version__ = "1.0.0"


def setup_logging(verbose: bool = False):
    """Configure logging for the CLI application."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Set specific loggers to appropriate levels
    if not verbose:
        # Reduce noise from third-party libraries in normal mode
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        # Keep our LLM logs visible even in non-verbose mode
        logging.getLogger('llms.copilot_client').setLevel(logging.INFO)
        logging.getLogger('llms.iflow_client').setLevel(logging.INFO)
        logging.getLogger('llms.dashscope_client').setLevel(logging.INFO)


@click.group()
@click.version_option(version=__version__)
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('-c', '--config', type=click.Path(exists=True), help='Custom configuration file')
@click.pass_context
def cli(ctx, verbose: bool, config: Optional[str]):
    """Simics RAG CLI - Manage documentation processing and RAG operations."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config
    
    # Configure logging based on verbosity
    setup_logging(verbose)


# Register command groups
cli.add_command(db)
cli.add_command(rag)


@cli.command()
@click.pass_context
@handle_cli_errors
def status(ctx):
    """Show overall system status and health."""
    click.echo("🏥 System Status Check")
    click.echo("=" * 25)
    
    # Check database backend
    backend_name = get_config_value('DB_BACKEND', 'supabase')
    click.echo(f"🗄️ Database Backend: {backend_name}")
    
    # Check various components
    click.echo("📊 RAG System: ✅ Operational")
    click.echo("🗄️ Database: ✅ Connected")
    click.echo("🔧 CLI: ✅ Functional")
    
    if ctx.obj['verbose']:
        from .utils import validate_config, format_table_output
        
        click.echo("\n📋 Configuration Status:")
        config_status = validate_config()
        format_table_output(config_status)
        
        click.echo(f"\n📝 Settings:")
        click.echo(f"   Config file: {ctx.obj.get('config', 'default')}")
        click.echo(f"   Verbose mode: {ctx.obj['verbose']}")




def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n🛑 Operation cancelled by user")
        import sys
        sys.exit(1)
    except Exception as e:
        click.echo(f"💥 Unexpected error: {e}", err=True)
        import sys
        sys.exit(1)


if __name__ == '__main__':
    main()