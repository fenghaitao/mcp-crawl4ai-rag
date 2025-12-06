"""
Abstract base classes defining interfaces for the chunking pipeline.

These interfaces enable a plugin architecture for different document types
and chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List
from .data_models import (
    DocumentStructure,
    Heading,
    CodeBlock,
    ProcessedChunk,
    ChunkMetadata,
)


class DocumentParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, content: str, source_path: str = "") -> DocumentStructure:
        """
        Parse document content into structured representation.
        
        Args:
            content: Raw document content as string
            source_path: Path to source file for metadata
            
        Returns:
            DocumentStructure with parsed headings, paragraphs, and code blocks
        """
        pass

    @abstractmethod
    def extract_headings(self, content: str) -> List[Heading]:
        """
        Extract heading hierarchy from document.
        
        Args:
            content: Raw document content
            
        Returns:
            List of Heading objects with parent relationships
        """
        pass

    @abstractmethod
    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Extract code blocks with language information.
        
        Args:
            content: Raw document content
            
        Returns:
            List of CodeBlock objects with language and location info
        """
        pass


class SemanticChunker(ABC):
    """Abstract base class for semantic chunking strategies."""

    @abstractmethod
    def chunk_document(self, doc_structure: DocumentStructure) -> List['DocumentChunk']:
        """
        Chunk document respecting semantic boundaries.
        
        Args:
            doc_structure: Parsed document structure
            
        Returns:
            List of DocumentChunk objects
        """
        pass

    @abstractmethod
    def should_split_section(self, section: 'Section') -> bool:
        """
        Determine if section exceeds size limits.
        
        Args:
            section: Section to evaluate
            
        Returns:
            True if section should be split
        """
        pass

    @abstractmethod
    def split_at_paragraph_boundary(self, section: 'Section') -> List['DocumentChunk']:
        """
        Split large section at paragraph boundaries.
        
        Args:
            section: Section to split
            
        Returns:
            List of DocumentChunk objects
        """
        pass


class MetadataExtractor(ABC):
    """Abstract base class for metadata extraction."""

    @abstractmethod
    def extract(self, chunk: 'DocumentChunk', doc_structure: DocumentStructure) -> ChunkMetadata:
        """
        Extract metadata for a chunk.
        
        Args:
            chunk: Document chunk to extract metadata from
            doc_structure: Full document structure for context
            
        Returns:
            ChunkMetadata object
        """
        pass

    @abstractmethod
    def build_heading_hierarchy(self, chunk: 'DocumentChunk') -> List[str]:
        """
        Build full heading path (H1 > H2 > H3).
        
        Args:
            chunk: Document chunk
            
        Returns:
            List of heading texts from root to current level
        """
        pass

    @abstractmethod
    def detect_code_language(self, code_block: CodeBlock) -> str:
        """
        Detect programming language in code block.
        
        Args:
            code_block: Code block to analyze
            
        Returns:
            Language identifier string
        """
        pass


# DocumentChunk is used by SemanticChunker but defined here to avoid circular imports
from dataclasses import dataclass
from .data_models import Section

@dataclass
class DocumentChunk:
    """Represents a chunk of a document before processing."""
    content: str
    section: Section
    chunk_index: int
    line_start: int
    line_end: int
