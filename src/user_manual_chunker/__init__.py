"""
User Manual Chunker - Intelligent chunking for technical documentation.

This package provides tools for parsing, chunking, and embedding technical
user manual documents optimized for Retrieval-Augmented Generation (RAG).
"""

from .data_models import (
    Heading,
    CodeBlock,
    Paragraph,
    DocumentStructure,
    Section,
    ChunkMetadata,
    ProcessedChunk,
)
from .interfaces import (
    DocumentParser,
    SemanticChunker,
    MetadataExtractor,
    DocumentChunk,
)
from .config import ChunkerConfig
from .markdown_parser import MarkdownParser
from .html_parser import HTMLParser
from .semantic_chunker import (
    SemanticChunker as SemanticChunkerImpl,
    PatternAwareSemanticChunker,
)
from .metadata_extractor import MetadataExtractor as MetadataExtractorImpl
from .pattern_handlers import (
    ListContextPreserver,
    APIDocumentationHandler,
    GrammarSpecificationHandler,
    DefinitionListHandler,
    TablePreserver,
    CrossReferencePreserver,
    PatternAwareChunker,
)
from .summary_generator import SummaryGenerator
from .embedding_generator import EmbeddingGenerator
from .orchestrator import UserManualChunker

__all__ = [
    "Heading",
    "CodeBlock",
    "Paragraph",
    "DocumentStructure",
    "Section",
    "ChunkMetadata",
    "ProcessedChunk",
    "DocumentParser",
    "SemanticChunker",
    "MetadataExtractor",
    "DocumentChunk",
    "ChunkerConfig",
    "MarkdownParser",
    "HTMLParser",
    "SemanticChunkerImpl",
    "PatternAwareSemanticChunker",
    "MetadataExtractorImpl",
    "ListContextPreserver",
    "APIDocumentationHandler",
    "GrammarSpecificationHandler",
    "DefinitionListHandler",
    "TablePreserver",
    "CrossReferencePreserver",
    "PatternAwareChunker",
    "SummaryGenerator",
    "EmbeddingGenerator",
    "UserManualChunker",
]
