"""
Markdown parser implementation for user manual chunking.

Parses markdown documents to extract structure including headings,
paragraphs, and code blocks.
"""

import re
import logging
from typing import List, Optional, Tuple
from .interfaces import DocumentParser
from .data_models import (
    DocumentStructure,
    Heading,
    CodeBlock,
    Paragraph,
)

logger = logging.getLogger(__name__)


class MarkdownParser(DocumentParser):
    """Parser for markdown documents."""
    
    # Regex patterns for markdown elements
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+?)(?:\s*\{#[^}]+\})?$', re.MULTILINE)
    CODE_FENCE_PATTERN = re.compile(
        r'^```(\w*)\s*\n(.*?)^```\s*$',
        re.MULTILINE | re.DOTALL
    )
    INDENTED_CODE_PATTERN = re.compile(
        r'^((?:    |\t).*(?:\n(?:    |\t).*|\n)*)',
        re.MULTILINE
    )
    
    def parse(self, content: str, source_path: str = "") -> DocumentStructure:
        """
        Parse markdown content into structured representation.
        
        Handles encoding issues, malformed markdown, and parsing errors gracefully.
        
        Args:
            content: Raw markdown content as string
            source_path: Path to source file for metadata
            
        Returns:
            DocumentStructure with parsed headings, paragraphs, and code blocks
            
        Raises:
            ValueError: If content is None or not a string
        """
        # Validate input
        if content is None:
            raise ValueError("Content cannot be None")
        
        if not isinstance(content, str):
            raise ValueError(f"Content must be a string, got {type(content)}")
        
        # Handle encoding issues - try to decode if bytes
        if isinstance(content, bytes):
            content = self._decode_content(content)
        
        # Handle empty content
        if not content.strip():
            logger.warning(f"Empty content for {source_path}")
            return DocumentStructure(
                source_path=source_path,
                headings=[],
                paragraphs=[],
                code_blocks=[],
                raw_content=content
            )
        
        # Extract code blocks FIRST to exclude them from heading extraction
        try:
            code_blocks = self.extract_code_blocks(content)
        except Exception as e:
            logger.warning(f"Error extracting code blocks from {source_path}: {e}")
            code_blocks = []
        
        # Extract headings, excluding lines inside code blocks
        try:
            headings = self.extract_headings(content, code_blocks)
        except Exception as e:
            logger.warning(f"Error extracting headings from {source_path}: {e}")
            headings = []
        
        try:
            paragraphs = self._extract_paragraphs(content, headings, code_blocks)
        except Exception as e:
            logger.warning(f"Error extracting paragraphs from {source_path}: {e}")
            paragraphs = []

        return DocumentStructure(
            source_path=source_path,
            headings=headings,
            paragraphs=paragraphs,
            code_blocks=code_blocks,
            raw_content=content
        )
    
    def _decode_content(self, content: bytes) -> str:
        """
        Decode bytes content trying multiple encodings.
        
        Args:
            content: Bytes content to decode
            
        Returns:
            Decoded string content
            
        Raises:
            ValueError: If content cannot be decoded with any encoding
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        
        # Last resort: decode with errors='replace'
        try:
            logger.warning(f"Could not decode with standard encodings, using utf-8 with replacement")
            return content.decode('utf-8', errors='replace')
        except Exception as e:
            raise ValueError(f"Failed to decode content: {e}")
    
    def extract_headings(self, content: str, code_blocks: List[CodeBlock] = None) -> List[Heading]:
        """
        Extract heading hierarchy from markdown document.
        
        Handles malformed headings gracefully.
        Excludes headings that appear inside code blocks.
        
        Args:
            content: Raw markdown content
            code_blocks: List of code blocks to exclude from heading extraction
            
        Returns:
            List of Heading objects with parent relationships
        """
        headings = []
        
        # Build set of line numbers that are inside code blocks
        code_block_lines = set()
        if code_blocks:
            for cb in code_blocks:
                for line_num in range(cb.line_start, cb.line_end + 1):
                    code_block_lines.add(line_num)
        
        try:
            lines = content.split('\n')
        except Exception as e:
            logger.error(f"Failed to split content into lines: {e}")
            return headings
        
        for line_num, line in enumerate(lines, start=1):
            # Skip lines inside code blocks
            if line_num in code_block_lines:
                continue
            
            try:
                match = self.HEADING_PATTERN.match(line)
                if match:
                    level = len(match.group(1))  # Count the # symbols
                    text = match.group(2).strip()
                    
                    # Validate heading level
                    if level < 1 or level > 6:
                        logger.warning(f"Invalid heading level {level} at line {line_num}, skipping")
                        continue
                    
                    # Validate heading text
                    if not text:
                        logger.warning(f"Empty heading text at line {line_num}, skipping")
                        continue
                    
                    heading = Heading(
                        level=level,
                        text=text,
                        line_number=line_num,
                        parent=None
                    )
                    headings.append(heading)
            except Exception as e:
                logger.warning(f"Error parsing heading at line {line_num}: {e}")
                continue
        # Build parent relationships
        try:
            self._build_heading_hierarchy(headings)
        except Exception as e:
            logger.warning(f"Error building heading hierarchy: {e}")
        return headings
    
    def _build_heading_hierarchy(self, headings: List[Heading]) -> None:
        """
        Build parent-child relationships between headings.
        
        Detects and handles circular references.
        
        Args:
            headings: List of headings to process (modified in place)
        """
        # Stack to track the current hierarchy
        stack: List[Heading] = []
        seen_headings = set()
        
        for heading in headings:
            # Detect circular references
            if id(heading) in seen_headings:
                logger.warning(f"Circular reference detected for heading: {heading.text}")
                continue
            seen_headings.add(id(heading))
            
            # Pop headings from stack that are at same or deeper level
            while stack and stack[-1].level >= heading.level:
                stack.pop()
            
            # The top of stack is now the parent (if any)
            if stack:
                # Verify parent is not the heading itself
                if stack[-1] is not heading:
                    heading.parent = stack[-1]
                else:
                    logger.warning(f"Self-reference detected for heading: {heading.text}")
            
            # Add current heading to stack
            stack.append(heading)
    
    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Extract code blocks with language information.
        
        Handles both triple-backtick fenced code blocks and indented code blocks.
        Handles malformed code blocks gracefully.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of CodeBlock objects with language and location info
        """
        code_blocks = []
        
        try:
            lines = content.split('\n')
        except Exception as e:
            logger.error(f"Failed to split content into lines: {e}")
            return code_blocks
        
        # Extract fenced code blocks (triple backticks)
        try:
            for match in self.CODE_FENCE_PATTERN.finditer(content):
                try:
                    language = match.group(1) or "text"
                    code_content = match.group(2)
                    
                    # If no language specified in fence, check first line for version string
                    if not language or language == "text":
                        # Check first non-empty line for language identifier like "dml 1.4"
                        first_line = None
                        for line in code_content.split('\n'):
                            if line.strip():
                                first_line = line.strip()
                                break
                        
                        if first_line:
                            # Check if first line matches pattern like "dml 1.4", "dml 1.2", etc.
                            dml_version_match = re.match(r'^\s*(dml)\s+\d+\.\d+', first_line, re.IGNORECASE)
                            if dml_version_match:
                                language = dml_version_match.group(1).lower()
                                logger.info(f"Detected language '{language}' from first line: {first_line}")
                    
                    # Find line numbers
                    start_pos = match.start()
                    end_pos = match.end()
                    line_start = content[:start_pos].count('\n') + 1
                    line_end = content[:end_pos].count('\n') + 1
                    
                    # Get preceding text (paragraph before code block)
                    preceding_text = self._get_preceding_text(content, start_pos, lines)
                    
                    code_blocks.append(CodeBlock(
                        content=code_content,
                        language=language,
                        line_start=line_start,
                        line_end=line_end,
                        preceding_text=preceding_text
                    ))
                except Exception as e:
                    logger.warning(f"Error extracting fenced code block: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error finding fenced code blocks: {e}")
        
        # Extract indented code blocks (4 spaces or tab)
        # Only if they're not already captured as fenced blocks
        fenced_ranges = [(cb.line_start, cb.line_end) for cb in code_blocks]
        
        current_block = []
        block_start_line = None
        
        for line_num, line in enumerate(lines, start=1):
            # Check if this line is already in a fenced code block
            in_fenced = any(start <= line_num <= end for start, end in fenced_ranges)
            
            if not in_fenced and (line.startswith('    ') or line.startswith('\t')):
                # This is an indented code line
                if block_start_line is None:
                    block_start_line = line_num
                # Remove the indentation
                code_line = line[4:] if line.startswith('    ') else line[1:]
                current_block.append(code_line)
            else:
                # Not an indented code line
                if current_block:
                    # Save the accumulated block
                    code_content = '\n'.join(current_block)
                    preceding_text = self._get_preceding_text_by_line(
                        lines, block_start_line - 1
                    )
                    
                    code_blocks.append(CodeBlock(
                        content=code_content,
                        language="text",
                        line_start=block_start_line,
                        line_end=line_num - 1,
                        preceding_text=preceding_text
                    ))
                    
                    current_block = []
                    block_start_line = None
        
        # Handle any remaining indented block at end of file
        if current_block:
            code_content = '\n'.join(current_block)
            preceding_text = self._get_preceding_text_by_line(
                lines, block_start_line - 1
            )
            
            code_blocks.append(CodeBlock(
                content=code_content,
                language="text",
                line_start=block_start_line,
                line_end=len(lines),
                preceding_text=preceding_text
            ))
        
        # Sort by line number
        code_blocks.sort(key=lambda cb: cb.line_start)
        
        return code_blocks
    
    def _get_preceding_text(
        self,
        content: str,
        code_start_pos: int,
        lines: List[str]
    ) -> Optional[str]:
        """
        Get the paragraph immediately preceding a code block.
        
        Args:
            content: Full document content
            code_start_pos: Character position where code block starts
            lines: Lines of the document
            
        Returns:
            Preceding paragraph text or None
        """
        # Find the line number where code starts
        line_num = content[:code_start_pos].count('\n')
        
        return self._get_preceding_text_by_line(lines, line_num)
    
    def _get_preceding_text_by_line(
        self,
        lines: List[str],
        code_line_num: int
    ) -> Optional[str]:
        """
        Get the paragraph immediately preceding a code block by line number.
        
        Args:
            lines: Lines of the document
            code_line_num: Line number where code starts (0-indexed)
            
        Returns:
            Preceding paragraph text or None
        """
        if code_line_num <= 0:
            return None
        
        # Look backwards for non-empty lines
        preceding_lines = []
        for i in range(code_line_num - 1, -1, -1):
            line = lines[i].strip()
            
            # Stop at empty line or heading
            if not line or line.startswith('#'):
                break
            
            # Stop at another code fence
            if line.startswith('```'):
                break
            
            preceding_lines.insert(0, lines[i])
        
        if preceding_lines:
            return '\n'.join(preceding_lines).strip()
        
        return None
    
    def _extract_paragraphs(
        self,
        content: str,
        headings: List[Heading],
        code_blocks: List[CodeBlock]
    ) -> List[Paragraph]:
        """
        Extract paragraphs from markdown content.
        
        Paragraphs are text blocks that are not headings or code blocks.
        
        Args:
            content: Raw markdown content
            headings: List of extracted headings
            code_blocks: List of extracted code blocks
            
        Returns:
            List of Paragraph objects
        """
        lines = content.split('\n')
        paragraphs = []
        
        # Build sets of line numbers that are headings or code blocks
        heading_lines = {h.line_number for h in headings}
        code_block_lines = set()
        for cb in code_blocks:
            for line_num in range(cb.line_start, cb.line_end + 1):
                code_block_lines.add(line_num)
        
        # Extract paragraphs
        current_para = []
        para_start_line = None
        
        for line_num, line in enumerate(lines, start=1):
            # Skip if this line is a heading or in a code block
            if line_num in heading_lines or line_num in code_block_lines:
                # Save accumulated paragraph
                if current_para:
                    para_text = '\n'.join(current_para).strip()
                    if para_text:  # Only save non-empty paragraphs
                        paragraphs.append(Paragraph(
                            content=para_text,
                            line_start=para_start_line,
                            line_end=line_num - 1
                        ))
                    current_para = []
                    para_start_line = None
                continue  # Skip this line completely
            
            if not line.strip():
                continue
            
            # Add line to current paragraph (including empty lines)
            if para_start_line is None:
                para_start_line = line_num
            current_para.append(line)
        
        # Handle any remaining paragraph at end of file
        if current_para:
            para_text = '\n'.join(current_para).strip()
            if para_text:
                paragraphs.append(Paragraph(
                    content=para_text,
                    line_start=para_start_line,
                    line_end=len(lines)
                ))

        return paragraphs
