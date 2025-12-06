"""
Mock chunker for testing document ingestion without dependencies.
"""

from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class MockMetadata:
    """Mock metadata for testing."""
    title: str = ""
    section: str = ""
    heading_hierarchy: List[str] = None
    word_count: int = 0
    has_code: bool = False
    language_hints: List[str] = None
    
    def __post_init__(self):
        if self.heading_hierarchy is None:
            self.heading_hierarchy = []
        if self.language_hints is None:
            self.language_hints = []

@dataclass 
class MockChunk:
    """Mock processed chunk for testing."""
    content: str
    metadata: MockMetadata
    embedding: Optional[List[float]] = None

class MockChunker:
    """Simple mock chunker for testing purposes."""
    
    def __init__(self):
        self.chunk_size = 1000
        self.overlap = 200
    
    def process_document(self, file_path: str, generate_embeddings: bool = True, generate_summaries: bool = False) -> List[MockChunk]:
        """Process a document and return mock chunks."""
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple chunking by paragraphs/sections
        chunks = []
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        chunk_num = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If adding this paragraph would exceed chunk size, create a chunk
            if current_chunk and len(current_chunk + para) > self.chunk_size:
                chunks.append(self._create_chunk(current_chunk, chunk_num, file_path))
                chunk_num += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_num, file_path))
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_num: int, file_path: str) -> MockChunk:
        """Create a mock chunk with metadata."""
        
        # Extract title from first line if it looks like a heading
        lines = content.strip().split('\n')
        title = ""
        section = ""
        
        for line in lines[:3]:  # Check first few lines
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                section = title
                break
        
        # Count words
        word_count = len(content.split())
        
        # Check for code blocks
        has_code = '```' in content or '    ' in content  # Simple heuristic
        
        metadata = MockMetadata(
            title=title,
            section=section,
            word_count=word_count,
            has_code=has_code
        )
        
        # Mock embedding (simple hash-based)
        embedding = None
        if True:  # Always generate for testing
            # Simple mock embedding - hash content to floats
            hash_val = hash(content)
            embedding = [float((hash_val + i) % 100) / 100.0 for i in range(1536)]
        
        return MockChunk(
            content=content.strip(),
            metadata=metadata,
            embedding=embedding
        )