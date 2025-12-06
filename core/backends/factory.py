"""
Database backend factory for creating appropriate backend instances.
"""

import os
from typing import Optional

from .base import DatabaseBackend
from .supabase import SupabaseBackend
from .chroma import ChromaBackend


def get_backend(backend_name: Optional[str] = None) -> DatabaseBackend:
    """
    Get database backend instance.
    
    Args:
        backend_name: 'supabase' or 'chroma'. If None, uses DB_BACKEND env var.
    
    Returns:
        DatabaseBackend instance
        
    Raises:
        ValueError: If backend name is unknown
        ImportError: If required dependencies are missing
        ConnectionError: If backend cannot be initialized
    """
    backend_name = backend_name or os.getenv('DB_BACKEND', 'supabase')
    
    if backend_name == 'supabase':
        return SupabaseBackend()
    elif backend_name == 'chroma':
        return ChromaBackend()
    else:
        raise ValueError(
            f"Unknown database backend: {backend_name}. "
            f"Supported backends: 'supabase', 'chroma'"
        )


def validate_backend_dependencies(backend_name: str) -> tuple[bool, str]:
    """
    Validate that required dependencies are available for a backend.
    
    Args:
        backend_name: Backend name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if backend_name == 'supabase':
        try:
            # Check if we can import supabase utilities
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))
            from utils import get_supabase_client
            return True, ""
        except ImportError as e:
            return False, f"Supabase dependencies missing: {e}"
    
    elif backend_name == 'chroma':
        try:
            import chromadb
            return True, ""
        except ImportError:
            return False, "ChromaDB import failed - this should not happen as it's a required dependency"
    
    else:
        return False, f"Unknown backend: {backend_name}"