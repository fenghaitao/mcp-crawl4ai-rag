"""
Semantic chunker implementation for user manual documents.

Intelligently chunks documents while preserving semantic coherence,
code block integrity, and contextual boundaries.
"""

import logging
from typing import List, Optional, Tuple
import re
from .interfaces import SemanticChunker as SemanticChunkerInterface, DocumentChunk
from .data_models import DocumentStructure, Section, Heading, Paragraph, CodeBlock
from .config import ChunkerConfig

logger = logging.getLogger(__name__)


class SemanticChunker(SemanticChunkerInterface):
    """
    Semantic chunker that respects document structure and code boundaries.
    
    This chunker:
    - Splits documents at section boundaries
    - Preserves code block integrity
    - Splits large sections at paragraph boundaries
    - Merges small sections
    - Creates overlapping chunks for context
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        chunk_overlap: int = 50,
        size_metric: str = "characters"
    ):
        """
        Initialize semantic chunker with configuration.
        
        Args:
            max_chunk_size: Maximum size of a chunk
            min_chunk_size: Minimum size of a chunk (for merging)
            chunk_overlap: Number of characters/tokens to overlap between chunks
            size_metric: Either "characters" or "tokens"
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap
        self.size_metric = size_metric
        
        if size_metric == "tokens":
            try:
                import tiktoken
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                raise ImportError(
                    "tiktoken is required for token-based chunking. "
                    "Install it with: pip install tiktoken"
                )
        else:
            self.tokenizer = None
    
    @classmethod
    def from_config(cls, config: ChunkerConfig) -> 'SemanticChunker':
        """Create chunker from configuration object."""
        return cls(
            max_chunk_size=config.max_chunk_size,
            min_chunk_size=config.min_chunk_size,
            chunk_overlap=config.chunk_overlap,
            size_metric=config.size_metric
        )
    
    def calculate_size(self, text: str) -> int:
        """
        Calculate size of text based on configured metric.
        
        Args:
            text: Text to measure
            
        Returns:
            Size in characters or tokens
        """
        if self.size_metric == "tokens":
            return len(self.tokenizer.encode(text))
        else:
            return len(text)
    
    def chunk_document(self, doc_structure: DocumentStructure) -> List[DocumentChunk]:
        """
        Chunk document respecting semantic boundaries.
        
        Handles empty sections, oversized code blocks, and circular references.
        
        Strategy:
        1. Extract sections from document structure
        2. For each section:
           - If too large: split at paragraph boundaries
           - If too small: mark for merging
        3. Merge small adjacent sections
        4. Apply overlap between chunks
        
        Args:
            doc_structure: Parsed document structure
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        
        # Validate input
        if not doc_structure:
            logger.warning("Empty document structure provided")
            return chunks
        
        # Extract sections from document
        try:
            sections = self._extract_sections(doc_structure)
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            sections = []
        
        if not sections:
            # Handle documents with no headings
            try:
                return self._chunk_flat_document(doc_structure)
            except Exception as e:
                logger.error(f"Error chunking flat document: {e}")
                return chunks
        
        # Process each section
        processed_sections = []
        for section in sections:
            try:
                # Skip empty sections
                if not section or not section.get_text_content().strip():
                    logger.info(f"Skipping empty section: {section.heading.text if section.heading else 'Unknown'}")
                    continue
                
                if self.should_split_section(section):
                    # Split large sections
                    split_chunks = self.split_at_paragraph_boundary(section)
                    processed_sections.extend(split_chunks)
                else:
                    # Keep section as is
                    processed_sections.append(section)
            except Exception as e:
                logger.warning(f"Error processing section: {e}")
                # Try to keep the section as-is
                processed_sections.append(section)
        
        # Merge small sections
        try:
            merged_sections = self._merge_small_sections(processed_sections)
        except Exception as e:
            logger.warning(f"Error merging sections: {e}")
            merged_sections = processed_sections
        
        # Convert sections to chunks
        for section in merged_sections:
            try:
                content = section.get_text_content()
                
                # Skip empty chunks
                if not content.strip():
                    logger.info("Skipping empty chunk")
                    continue
                
                # Calculate chunk size
                chunk_size = self.calculate_size(content)
                
                # Validate chunk size
                if chunk_size > self.max_chunk_size:
                    logger.error(
                        f"Chunk {chunk_index} exceeds max_chunk_size: "
                        f"{chunk_size} > {self.max_chunk_size} "
                        f"(section: {section.heading.text if section.heading else 'unknown'})"
                    )
                
                chunk = DocumentChunk(
                    content=content,
                    section=section,
                    chunk_index=chunk_index,
                    line_start=section.heading.line_number if section.heading else 0,
                    line_end=self._get_section_end_line(section),
                    chunk_size=chunk_size
                )
                chunks.append(chunk)
                chunk_index += 1
            except Exception as e:
                logger.warning(f"Error creating chunk: {e}")
                continue
        
        # Apply overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            try:
                chunks = self._apply_overlap(chunks)
            except Exception as e:
                logger.warning(f"Error applying overlap: {e}")
        
        # Log chunk size statistics
        if chunks:
            chunk_sizes = [chunk.chunk_size for chunk in chunks]
            logger.info(
                f"Created {len(chunks)} chunks: "
                f"min={min(chunk_sizes)}, "
                f"max={max(chunk_sizes)}, "
                f"avg={sum(chunk_sizes)//len(chunk_sizes)}, "
                f"limit={self.max_chunk_size}"
            )
            
            oversized_count = sum(1 for size in chunk_sizes if size > self.max_chunk_size)
            if oversized_count > 0:
                logger.warning(f"{oversized_count} chunks exceed max_chunk_size")
        
        return chunks
    
    def should_split_section(self, section: Section) -> bool:
        """
        Determine if section exceeds size limits.
        
        Args:
            section: Section to evaluate
            
        Returns:
            True if section should be split
        """
        content = section.get_text_content()
        size = self.calculate_size(content)
        return size > self.max_chunk_size
    
    def split_at_paragraph_boundary(self, section: Section) -> List[Section]:
        """
        Split large section at paragraph boundaries.
        
        Handles oversized code blocks and paragraphs by creating dedicated chunks with warnings.
        
        Strategy:
        - Never split code blocks or paragraphs internally
        - Keep code blocks with preceding explanatory text
        - Split at content boundaries
        - Include section heading in each split
        - Handle oversized content specially
        
        Args:
            section: Section to split
            
        Returns:
            List of Section objects (split chunks)
        """
        split_sections = []
        current_paragraphs = []
        current_code_blocks = []
        
        # Get heading size (will be included in each split)
        heading_text = f"{'#' * section.heading.level} {section.heading.text}\n"
        heading_size = self.calculate_size(heading_text)
        
        # Initialize with heading size since it's added to every split
        current_size = heading_size
        
        # Interleave paragraphs and code blocks by line number
        content_items = []
        for p in section.paragraphs:
            content_items.append(('paragraph', p))
        for cb in section.code_blocks:
            content_items.append(('code', cb))
        content_items.sort(key=lambda x: x[1].line_start)
        
        for content_type, content in content_items:
            if content_type == 'code':
                # Code blocks must stay intact with preceding text
                code_text = f"\n```{content.language}\n{content.content}\n```\n"
                code_size = self.calculate_size(code_text)
                
                # Handle oversized code blocks
                if code_size > self.max_chunk_size:
                    logger.warning(
                        f"Code block at line {content.line_start} exceeds max_chunk_size "
                        f"({code_size} > {self.max_chunk_size}). Creating dedicated chunk."
                    )
                    
                    # Save current accumulated content if any
                    if current_paragraphs or current_code_blocks:
                        split_sections.append(self._create_split_section(
                            section.heading, current_paragraphs, current_code_blocks
                        ))
                        current_paragraphs = []
                        current_code_blocks = []
                        current_size = heading_size  # Reset to heading size
                    
                    # Create a dedicated chunk for this oversized code block
                    split_sections.append(self._create_split_section(
                        section.heading, [], [content]
                    ))
                    continue
                
                # Check if adding this code block would exceed limit
                if current_size + code_size > self.max_chunk_size and (current_paragraphs or current_code_blocks):
                    logger.warning(f"Adding this code block exceeds max_chunk_size, "
                                   f"{current_size+code_size} > {self.max_chunk_size}. Creating new chunk.")
                    # Create a chunk with what we have so far
                    split_sections.append(self._create_split_section(
                        section.heading, current_paragraphs, current_code_blocks
                    ))
                    current_paragraphs = []
                    current_code_blocks = []
                    current_size = heading_size  # Reset to heading size
                
                # Add code block to current chunk
                current_code_blocks.append(content)
                current_size += code_size
                
            else:  # paragraph
                para_size = self.calculate_size(content.content)
                
                # Handle oversized paragraphs
                if para_size > self.max_chunk_size:
                    logger.warning(
                        f"Paragraph at line {content.line_start} exceeds max_chunk_size "
                        f"({para_size} > {self.max_chunk_size}). Creating dedicated chunk."
                    )
                    
                    # Save current accumulated content if any
                    if current_paragraphs or current_code_blocks:
                        split_sections.append(self._create_split_section(
                            section.heading, current_paragraphs, current_code_blocks
                        ))
                        current_paragraphs = []
                        current_code_blocks = []
                        current_size = heading_size  # Reset to heading size
                    
                    # Create a dedicated chunk for this oversized paragraph
                    split_sections.append(self._create_split_section(
                        section.heading, [content], []
                    ))
                    continue
                
                # Check if adding this paragraph would exceed limit
                if current_size + para_size > self.max_chunk_size and (current_paragraphs or current_code_blocks):
                    # Create a chunk with what we have so far
                    logger.warning(f"Adding this paragraph exceeds max_chunk_size, "
                                   f"{current_size+para_size} > {self.max_chunk_size}. Creating new chunk.")
                    split_sections.append(self._create_split_section(
                        section.heading, current_paragraphs, current_code_blocks
                    ))
                    current_paragraphs = []
                    current_code_blocks = []
                    current_size = heading_size  # Reset to heading size
                
                # Add paragraph to current chunk
                current_paragraphs.append(content)
                current_size += para_size
        
        # Add remaining content as final chunk
        if current_paragraphs or current_code_blocks:
            split_sections.append(self._create_split_section(
                section.heading, current_paragraphs, current_code_blocks
            ))

        return split_sections if split_sections else [section]

    
    def _extract_sections(self, doc_structure: DocumentStructure) -> List[Section]:
        """
        Extract sections from document structure.
        
        Args:
            doc_structure: Document structure
            
        Returns:
            List of Section objects
        """
        sections = []
        for heading in doc_structure.headings:
            section = doc_structure.get_section(heading)
            sections.append(section)
        return sections
    
    def _chunk_flat_document(self, doc_structure: DocumentStructure) -> List[DocumentChunk]:
        """
        Handle documents with no headings by chunking at paragraph boundaries.
        
        Args:
            doc_structure: Document structure
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        current_paragraphs = []
        current_code_blocks = []
        current_size = 0
        
        # Interleave paragraphs and code blocks
        content_items = []
        for p in doc_structure.paragraphs:
            content_items.append(('paragraph', p))
        for cb in doc_structure.code_blocks:
            content_items.append(('code', cb))
        content_items.sort(key=lambda x: x[1].line_start)
        
        for content_type, content in content_items:
            if content_type == 'code':
                code_text = f"\n```{content.language}\n{content.content}\n```\n"
                code_size = self.calculate_size(code_text)
                
                if current_size + code_size > self.max_chunk_size and current_paragraphs:
                    # Create chunk
                    chunks.append(self._create_flat_chunk(
                        current_paragraphs, current_code_blocks, chunk_index
                    ))
                    chunk_index += 1
                    current_paragraphs = []
                    current_code_blocks = []
                    current_size = 0
                
                current_code_blocks.append(content)
                current_size += code_size
                
            else:  # paragraph
                para_size = self.calculate_size(content.content)
                
                if current_size + para_size > self.max_chunk_size and current_paragraphs:
                    # Create chunk
                    chunks.append(self._create_flat_chunk(
                        current_paragraphs, current_code_blocks, chunk_index
                    ))
                    chunk_index += 1
                    current_paragraphs = []
                    current_code_blocks = []
                    current_size = 0
                
                current_paragraphs.append(content)
                current_size += para_size
        
        # Add remaining content
        if current_paragraphs or current_code_blocks:
            chunks.append(self._create_flat_chunk(
                current_paragraphs, current_code_blocks, chunk_index
            ))
        
        return chunks
    
    def _create_split_section(
        self,
        heading: Heading,
        paragraphs: List[Paragraph],
        code_blocks: List[CodeBlock]
    ) -> Section:
        """
        Create a section from split content.
        
        Args:
            heading: Section heading
            paragraphs: Paragraphs in this split
            code_blocks: Code blocks in this split
            
        Returns:
            Section object
        """
        return Section(
            heading=heading,
            paragraphs=paragraphs,
            code_blocks=code_blocks
        )
    
    def _create_flat_chunk(
        self,
        paragraphs: List[Paragraph],
        code_blocks: List[CodeBlock],
        chunk_index: int
    ) -> DocumentChunk:
        """
        Create a chunk from flat document content.
        
        Args:
            paragraphs: Paragraphs in chunk
            code_blocks: Code blocks in chunk
            chunk_index: Index of this chunk
            
        Returns:
            DocumentChunk object
        """
        # Create a dummy heading for flat content
        dummy_heading = Heading(
            level=1,
            text="Document Content",
            line_number=paragraphs[0].line_start if paragraphs else (
                code_blocks[0].line_start if code_blocks else 0
            )
        )
        
        section = Section(
            heading=dummy_heading,
            paragraphs=paragraphs,
            code_blocks=code_blocks
        )
        
        line_start = min(
            [p.line_start for p in paragraphs] + [cb.line_start for cb in code_blocks]
        )
        line_end = max(
            [p.line_end for p in paragraphs] + [cb.line_end for cb in code_blocks]
        )
        
        content = section.get_text_content()
        chunk_size = self.calculate_size(content)
        
        return DocumentChunk(
            content=content,
            section=section,
            chunk_index=chunk_index,
            line_start=line_start,
            line_end=line_end,
            chunk_size=chunk_size
        )
    
    def _merge_small_sections(self, sections: List[Section]) -> List[Section]:
        """
        Merge sections smaller than min_chunk_size with adjacent sections.
        
        Strategy:
        - Merge small sections with next section at same or lower level
        - Respect semantic boundaries (don't merge across major headings)
        
        Args:
            sections: List of sections to potentially merge
            
        Returns:
            List of sections after merging
        """
        if not sections:
            return sections
        
        merged = []
        i = 0
        
        while i < len(sections):
            current_section = sections[i]
            current_size = self.calculate_size(current_section.get_text_content())
            
            # Check if current section is too small
            if current_size < self.min_chunk_size and i + 1 < len(sections):
                next_section = sections[i + 1]
                
                # Only merge if next section is at same or lower level
                if next_section.heading.level >= current_section.heading.level:
                    # Merge current with next
                    merged_section = self._merge_two_sections(current_section, next_section)
                    merged.append(merged_section)
                    i += 2  # Skip next section since we merged it
                    continue
            
            merged.append(current_section)
            i += 1
        
        return merged
    
    def _merge_two_sections(self, section1: Section, section2: Section) -> Section:
        """
        Merge two sections into one.
        
        Args:
            section1: First section
            section2: Second section
            
        Returns:
            Merged section
        """
        # Use the first section's heading
        return Section(
            heading=section1.heading,
            paragraphs=section1.paragraphs + section2.paragraphs,
            code_blocks=section1.code_blocks + section2.code_blocks
        )
    
    def _apply_overlap(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Apply overlap between adjacent chunks.
        
        Strategy:
        - Take last N characters/tokens from previous chunk
        - Ensure overlap includes complete sentences
        - Prepend to next chunk
        
        Args:
            chunks: List of chunks
            
        Returns:
            List of chunks with overlap applied
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk has no overlap
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            # Extract overlap from previous chunk
            overlap_text = self._extract_overlap(prev_chunk.content, self.chunk_overlap)
            
            # Prepend overlap to current chunk
            new_content = overlap_text + "\n\n" + current_chunk.content if overlap_text else current_chunk.content
            
            # Recalculate chunk size with overlap
            new_chunk_size = self.calculate_size(new_content)
            
            overlapped_chunk = DocumentChunk(
                content=new_content,
                section=current_chunk.section,
                chunk_index=current_chunk.chunk_index,
                line_start=current_chunk.line_start,
                line_end=current_chunk.line_end,
                chunk_size=new_chunk_size
            )
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _extract_overlap(self, text: str, overlap_size: int) -> str:
        """
        Extract overlap text from end of previous chunk.
        
        Ensures overlap includes complete sentences and doesn't break code blocks.
        
        Args:
            text: Text to extract from
            overlap_size: Desired overlap size
            
        Returns:
            Overlap text
        """
        if self.size_metric == "tokens":
            # For tokens, we need to decode back to text
            tokens = self.tokenizer.encode(text)
            if len(tokens) <= overlap_size:
                return text
            
            overlap_tokens = tokens[-overlap_size:]
            overlap_text = self.tokenizer.decode(overlap_tokens)
        else:
            # For characters
            if len(text) <= overlap_size:
                return text
            
            overlap_text = text[-overlap_size:]
        
        # Check if overlap would break a code block
        # Count code fences in the overlap
        fence_count = overlap_text.count("```")
        if fence_count % 2 != 0:
            # Odd number of fences means we're in the middle of a code block
            # Don't include any overlap that breaks code blocks
            return ""
        
        # Ensure we start at a sentence boundary
        overlap_text = self._trim_to_sentence_boundary(overlap_text)
        
        return overlap_text
    
    def _trim_to_sentence_boundary(self, text: str) -> str:
        """
        Trim text to start at a sentence boundary.
        
        Args:
            text: Text to trim
            
        Returns:
            Text starting at sentence boundary
        """
        # Find first sentence boundary (., !, ?, or newline)
        sentence_pattern = r'[.!?\n]\s+'
        match = re.search(sentence_pattern, text)
        
        if match:
            # Start after the sentence boundary
            return text[match.end():]
        
        # If no sentence boundary found, return as is
        return text
    
    def _get_section_end_line(self, section: Section) -> int:
        """
        Get the last line number of a section.
        
        Args:
            section: Section to analyze
            
        Returns:
            Last line number
        """
        max_line = section.heading.line_number
        
        for p in section.paragraphs:
            max_line = max(max_line, p.line_end)
        
        for cb in section.code_blocks:
            max_line = max(max_line, cb.line_end)
        
        return max_line



class PatternAwareSemanticChunker(SemanticChunker):
    """
    Enhanced semantic chunker that respects special documentation patterns.
    
    This chunker extends SemanticChunker with pattern awareness to ensure
    special structures (API docs, grammar rules, tables, etc.) are kept
    together during chunking.
    
    Features:
    - All features from SemanticChunker
    - Detects and preserves list structures
    - Keeps API documentation patterns together
    - Preserves grammar rules with examples
    - Keeps definition lists intact
    - Preserves table structures
    - Maintains cross-reference links
    """
    
    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        chunk_overlap: int = 50,
        size_metric: str = "characters",
        enable_pattern_detection: bool = True
    ):
        """
        Initialize pattern-aware semantic chunker.
        
        Args:
            max_chunk_size: Maximum size of a chunk
            min_chunk_size: Minimum size of a chunk (for merging)
            chunk_overlap: Number of characters/tokens to overlap between chunks
            size_metric: Either "characters" or "tokens"
            enable_pattern_detection: Whether to enable pattern detection
        """
        super().__init__(max_chunk_size, min_chunk_size, chunk_overlap, size_metric)
        
        self.enable_pattern_detection = enable_pattern_detection
        
        if enable_pattern_detection:
            # Import here to avoid circular dependency
            from .pattern_handlers import PatternAwareChunker
            self.pattern_analyzer = PatternAwareChunker()
        else:
            self.pattern_analyzer = None
        
        # Cache for detected patterns
        self._patterns_cache = None
    
    @classmethod
    def from_config(cls, config: ChunkerConfig, enable_patterns: bool = True) -> 'PatternAwareSemanticChunker':
        """
        Create pattern-aware chunker from configuration object.
        
        Args:
            config: Configuration object
            enable_patterns: Whether to enable pattern detection
            
        Returns:
            PatternAwareSemanticChunker instance
        """
        return cls(
            max_chunk_size=config.max_chunk_size,
            min_chunk_size=config.min_chunk_size,
            chunk_overlap=config.chunk_overlap,
            size_metric=config.size_metric,
            enable_pattern_detection=enable_patterns
        )
    
    def chunk_document(self, doc_structure: DocumentStructure) -> List[DocumentChunk]:
        """
        Chunk document with pattern awareness.
        
        First analyzes the document for special patterns, then uses this
        information to make intelligent chunking decisions.
        
        Args:
            doc_structure: Parsed document structure
            
        Returns:
            List of DocumentChunk objects
        """
        # Analyze patterns if enabled
        if self.enable_pattern_detection and self.pattern_analyzer:
            self._patterns_cache = self.pattern_analyzer.analyze_content(
                doc_structure.raw_content,
                doc_structure.paragraphs,
                doc_structure.code_blocks
            )
        else:
            self._patterns_cache = None
        
        # Use parent's chunking logic
        chunks = super().chunk_document(doc_structure)
        
        # Clear cache
        self._patterns_cache = None
        
        return chunks
    
    def split_at_paragraph_boundary(self, section: Section) -> List[Section]:
        """
        Split large section at paragraph boundaries with pattern awareness.
        
        This override adds pattern detection to prevent splitting within
        special structures like API docs, tables, or grammar rules.
        
        Args:
            section: Section to split
            
        Returns:
            List of Section objects (split chunks)
        """
        # If pattern detection is disabled, use parent's logic
        if not self.enable_pattern_detection or not self._patterns_cache:
            return super().split_at_paragraph_boundary(section)
        
        split_sections = []
        current_paragraphs = []
        current_code_blocks = []
        current_size = 0
        
        # Get heading size
        heading_text = f"{'#' * section.heading.level} {section.heading.text}\n"
        heading_size = self.calculate_size(heading_text)
        
        # Interleave paragraphs and code blocks by line number
        content_items = []
        for p in section.paragraphs:
            content_items.append(('paragraph', p))
        for cb in section.code_blocks:
            content_items.append(('code', cb))
        content_items.sort(key=lambda x: x[1].line_start)
        
        # Track the start of current accumulation
        current_start_line = None
        
        for content_type, content in content_items:
            if current_start_line is None:
                current_start_line = content.line_start
            
            if content_type == 'code':
                code_text = f"\n```{content.language}\n{content.content}\n```\n"
                code_size = self.calculate_size(code_text)
                
                # Check if we should split before this code block
                if current_size + heading_size + code_size > self.max_chunk_size and current_paragraphs:
                    # Check if current range contains patterns that should stay together
                    should_keep = self.pattern_analyzer.should_keep_together(
                        current_start_line,
                        content.line_start - 1,
                        self._patterns_cache,
                        self.max_chunk_size
                    )
                    
                    if not should_keep:
                        # Safe to split - create chunk with accumulated content
                        split_sections.append(self._create_split_section(
                            section.heading, current_paragraphs, current_code_blocks
                        ))
                        current_paragraphs = []
                        current_code_blocks = []
                        current_size = 0
                        current_start_line = content.line_start
                
                current_code_blocks.append(content)
                current_size += code_size
                
            else:  # paragraph
                para_size = self.calculate_size(content.content)
                
                # Check if we should split before this paragraph
                if current_size + heading_size + para_size > self.max_chunk_size and current_paragraphs:
                    # Check if current range contains patterns that should stay together
                    should_keep = self.pattern_analyzer.should_keep_together(
                        current_start_line,
                        content.line_start - 1,
                        self._patterns_cache,
                        self.max_chunk_size
                    )
                    
                    if not should_keep:
                        # Safe to split - create chunk with accumulated content
                        split_sections.append(self._create_split_section(
                            section.heading, current_paragraphs, current_code_blocks
                        ))
                        current_paragraphs = []
                        current_code_blocks = []
                        current_size = 0
                        current_start_line = content.line_start
                
                current_paragraphs.append(content)
                current_size += para_size
        
        # Add remaining content as final chunk
        if current_paragraphs or current_code_blocks:
            split_sections.append(self._create_split_section(
                section.heading, current_paragraphs, current_code_blocks
            ))
        
        return split_sections if split_sections else [section]
    
    def get_detected_patterns(self) -> Optional[dict]:
        """
        Get the currently cached pattern detection results.
        
        Returns:
            Dictionary of detected patterns, or None if not available
        """
        return self._patterns_cache
    
    def get_pattern_statistics(self) -> dict:
        """
        Get statistics about detected patterns.
        
        Returns:
            Dictionary with pattern counts
        """
        if not self._patterns_cache:
            return {
                'lists': 0,
                'api_docs': 0,
                'grammar_rules': 0,
                'definitions': 0,
                'tables': 0,
                'references': 0,
                'total': 0
            }
        
        stats = {
            'lists': len(self._patterns_cache.get('lists', [])),
            'api_docs': len(self._patterns_cache.get('api_docs', [])),
            'grammar_rules': len(self._patterns_cache.get('grammar_rules', [])),
            'definitions': len(self._patterns_cache.get('definitions', [])),
            'tables': len(self._patterns_cache.get('tables', [])),
            'references': len(self._patterns_cache.get('references', []))
        }
        stats['total'] = sum(stats.values())
        
        return stats
