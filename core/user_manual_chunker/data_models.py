"""
Data models for user manual chunking.

Defines the core data structures used throughout the chunking pipeline.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
import numpy as np


@dataclass
class Heading:
    """Represents a heading in a document."""
    level: int  # 1-6 for H1-H6
    text: str
    line_number: int
    parent: Optional['Heading'] = None

    def __post_init__(self):
        if not 1 <= self.level <= 6:
            raise ValueError(f"Heading level must be between 1 and 6, got {self.level}")


@dataclass
class CodeBlock:
    """Represents a code block in a document."""
    content: str
    language: str
    line_start: int
    line_end: int
    preceding_text: Optional[str] = None  # Explanatory text before code

    def __post_init__(self):
        if self.line_start > self.line_end:
            raise ValueError(f"line_start ({self.line_start}) cannot be greater than line_end ({self.line_end})")


@dataclass
class Paragraph:
    """Represents a paragraph in a document."""
    content: str
    line_start: int
    line_end: int

    def __post_init__(self):
        if self.line_start > self.line_end:
            raise ValueError(f"line_start ({self.line_start}) cannot be greater than line_end ({self.line_end})")


@dataclass
class DocumentStructure:
    """Unified representation of a parsed document."""
    source_path: str
    headings: List[Heading] = field(default_factory=list)
    paragraphs: List[Paragraph] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)
    raw_content: str = ""

    def get_section(self, heading: Heading) -> 'Section':
        """Get all content under a heading until next same-level heading."""
        # Find the start line of this heading
        start_line = heading.line_number
        
        # Find the end line (next heading at same or higher level)
        end_line = float('inf')
        for h in self.headings:
            if h.line_number > heading.line_number and h.level <= heading.level:
                end_line = h.line_number
                break
        
        # Collect content within this range
        section_paragraphs = [p for p in self.paragraphs 
                             if start_line <= p.line_start < end_line]
        section_code_blocks = [cb for cb in self.code_blocks 
                              if start_line <= cb.line_start < end_line]
        
        return Section(
            heading=heading,
            paragraphs=section_paragraphs,
            code_blocks=section_code_blocks
        )


@dataclass
class Section:
    """Represents a section of a document (heading + content)."""
    heading: Heading
    paragraphs: List[Paragraph] = field(default_factory=list)
    code_blocks: List[CodeBlock] = field(default_factory=list)

    def get_text_content(self) -> str:
        """Get the full text content of this section."""
        parts = [f"{'#' * self.heading.level} {self.heading.text}\n"]
        
        # Interleave paragraphs and code blocks by line number
        all_content = []
        for p in self.paragraphs:
            all_content.append((p.line_start, 'paragraph', p))
        for cb in self.code_blocks:
            all_content.append((cb.line_start, 'code', cb))
        
        all_content.sort(key=lambda x: x[0])
        
        for _, content_type, content in all_content:
            if content_type == 'paragraph':
                parts.append(content.content)
            else:  # code block
                parts.append(f"\n```{content.language}\n{content.content}\n```\n")
        
        return "\n".join(parts)

    def char_count(self) -> int:
        """Calculate character count of this section."""
        return len(self.get_text_content())


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    source_file: str
    heading_hierarchy: List[str]  # ["Introduction", "Language Features", "Data Types"]
    section_level: int  # Depth in document hierarchy
    contains_code: bool
    code_languages: List[str]  # ["dml", "python"]
    chunk_index: int  # Position in document
    line_start: int
    line_end: int
    char_count: int
    token_count: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ProcessedChunk:
    """Complete chunk with all generated data."""
    chunk_id: str  # Unique identifier
    content: str  # Chunk text
    metadata: ChunkMetadata
    summary: Optional[str] = None
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "summary": self.summary,
            "embedding": self.embedding.tolist() if self.embedding is not None else None
        }
