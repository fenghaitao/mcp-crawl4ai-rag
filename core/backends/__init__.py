"""
Database backend abstractions and implementations.

This package provides a unified interface for different database backends
including Supabase and ChromaDB.
"""

from .base import DatabaseBackend
from .factory import get_backend

__all__ = ['DatabaseBackend', 'get_backend']