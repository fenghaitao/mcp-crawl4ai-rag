"""
Core module for Simics RAG system.

This package provides unified access to all core functionality including
CLI commands, database operations, and RAG pipeline components.
"""

__version__ = "1.0.0"

# Import main CLI for convenience
from .cli.main import main as cli_main

__all__ = ['cli_main']