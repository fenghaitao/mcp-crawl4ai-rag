#!/usr/bin/env python3
"""
Main entry point for the Simics RAG and Knowledge Graph CLI.

This module serves as the primary interface for all CLI operations including:
- RAG pipeline operations (crawling, chunking, querying)
- Knowledge graph management
- Database operations
- Development utilities

Usage:
    python __main__.py --help
    python __main__.py crawl --help
    python __main__.py query "your question"
    python __main__.py kg ingest-dml /path/to/file.dml
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from .cli import main
    main()