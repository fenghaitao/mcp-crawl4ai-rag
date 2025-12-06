"""
CLI utilities for error handling, configuration, and common functions.
"""

import functools
import traceback
import sys
from typing import Callable, Any, Dict, Optional

import click

# Load environment variables at module level
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass


def handle_cli_errors(func: Callable) -> Callable:
    """
    Decorator to handle CLI command errors consistently.
    
    Args:
        func: CLI command function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            click.echo("\n🛑 Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            ctx = click.get_current_context()
            click.echo(f"❌ Error: {e}", err=True)
            if ctx.obj and ctx.obj.get('verbose'):
                click.echo(f"\n📋 Traceback:", err=True)
                click.echo(traceback.format_exc(), err=True)
            sys.exit(1)
    return wrapper


def verbose_echo(ctx: click.Context, message: str):
    """
    Echo message only if verbose mode is enabled.
    
    Args:
        ctx: Click context
        message: Message to echo
    """
    if ctx.obj and ctx.obj.get('verbose'):
        click.echo(message)


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get configuration value from environment or default.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    import os
    return os.getenv(key, default)


def validate_config() -> Dict[str, str]:
    """
    Validate system configuration and return status.
    
    Returns:
        Dictionary with configuration validation results
    """
    import os
    from pathlib import Path
    
    config_status = {}
    
    # Check database backend configuration
    db_backend = os.getenv('DB_BACKEND', 'supabase')
    config_status['db_backend'] = db_backend
    
    if db_backend == 'supabase':
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        config_status['supabase_url'] = '✅ Set' if supabase_url else '❌ Missing'
        config_status['supabase_key'] = '✅ Set' if supabase_key else '❌ Missing'
    
    elif db_backend == 'chroma':
        chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        config_status['chroma_path'] = chroma_path
        config_status['chroma_exists'] = '✅ Yes' if Path(chroma_path).exists() else '❌ No'
    
    return config_status


def format_table_output(data: Dict[str, Any], title: str = None) -> None:
    """
    Format and display table-like data.
    
    Args:
        data: Dictionary of key-value pairs
        title: Optional title for the table
    """
    if title:
        click.echo(f"\n{title}")
        click.echo("=" * len(title))
    
    max_key_len = max(len(str(k)) for k in data.keys()) if data else 0
    
    for key, value in data.items():
        click.echo(f"{str(key).ljust(max_key_len + 2)}: {value}")


def confirm_destructive_action(action_name: str, target: Optional[str] = None) -> bool:
    """
    Confirm destructive actions with the user.
    
    Args:
        action_name: Name of the action (e.g., "delete")
        target: Optional target specification
        
    Returns:
        True if user confirms, False otherwise
    """
    target_text = f" from {target}" if target else ""
    return click.confirm(f"⚠️  Are you sure you want to {action_name}{target_text}?")