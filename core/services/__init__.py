"""
Core services for RAG operations.

This package contains reusable business logic services that bridge
the CLI commands with the underlying processing libraries.
"""

from .document_ingest_service import DocumentIngestService

__all__ = [
    'DocumentIngestService'
]