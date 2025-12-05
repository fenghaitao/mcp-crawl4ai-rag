"""
Metadata extractor implementation for user manual chunks.

Extracts hierarchical metadata including heading hierarchy, code language detection,
and document provenance information.
"""

from typing import List, Set
import re
from .interfaces import MetadataExtractor as MetadataExtractorInterface, DocumentChunk
from .data_models import DocumentStructure, ChunkMetadata, CodeBlock, Heading


class MetadataExtractor(MetadataExtractorInterface):
    """
    Metadata extractor that builds hierarchical metadata for chunks.
    
    This extractor:
    - Builds full heading hierarchy paths
    - Detects programming languages in code blocks
    - Records source file information
    - Calculates section depth
    - Identifies code presence
    """
    
    def __init__(self):
        """Initialize metadata extractor."""
        # Common language keywords for detection
        self.language_patterns = {
            'python': [r'\bdef\b', r'\bclass\b', r'\bimport\b', r'\bfrom\b', r'\bprint\b'],
            'javascript': [r'\bfunction\b', r'\bconst\b', r'\blet\b', r'\bvar\b', r'\bconsole\.log\b'],
            'java': [r'\bpublic\b', r'\bprivate\b', r'\bclass\b', r'\bvoid\b', r'\bstatic\b'],
            'c': [r'\bint\b', r'\bvoid\b', r'\bchar\b', r'\bstruct\b', r'#include'],
            'cpp': [r'\bnamespace\b', r'\btemplate\b', r'\bclass\b', r'#include', r'\bstd::'],
            'dml': [r'\bdevice\b', r'\bbank\b', r'\bregister\b', r'\bmethod\b', r'\btemplate\b'],
            'rust': [r'\bfn\b', r'\blet\b', r'\bmut\b', r'\bimpl\b', r'\bstruct\b'],
            'go': [r'\bfunc\b', r'\bpackage\b', r'\bimport\b', r'\btype\b', r'\bvar\b'],
            'ruby': [r'\bdef\b', r'\bend\b', r'\bclass\b', r'\bmodule\b', r'\brequire\b'],
            'php': [r'<\?php', r'\bfunction\b', r'\bclass\b', r'\bnamespace\b', r'\$\w+'],
            'shell': [r'\becho\b', r'\bexport\b', r'\bif\b.*\bthen\b', r'\bfi\b', r'#!/bin/'],
            'sql': [r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bINSERT\b', r'\bUPDATE\b'],
            'html': [r'<html', r'<div', r'<body', r'<head', r'<p>'],
            'css': [r'\{[^}]*:[^}]*\}', r'@media', r'\.[\w-]+\s*\{'],
            'json': [r'^\s*\{', r'^\s*\[', r'"\w+"\s*:'],
            'yaml': [r'^\w+:', r'^\s+-\s+\w+', r'---'],
            'markdown': [r'^#+\s', r'\[.*\]\(.*\)', r'```'],
        }
    
    def extract(self, chunk: DocumentChunk, doc_structure: DocumentStructure) -> ChunkMetadata:
        """
        Extract metadata for a chunk.
        
        Args:
            chunk: Document chunk to extract metadata from
            doc_structure: Full document structure for context
            
        Returns:
            ChunkMetadata object with all extracted information
        """
        # Build heading hierarchy
        heading_hierarchy = self.build_heading_hierarchy(chunk)
        
        # Calculate section level
        section_level = len(heading_hierarchy)
        
        # Detect code blocks and languages
        code_blocks = chunk.section.code_blocks
        contains_code = len(code_blocks) > 0
        code_languages = []
        
        for code_block in code_blocks:
            language = self.detect_code_language(code_block)
            if language and language not in code_languages:
                code_languages.append(language)
        
        # Calculate character count
        char_count = len(chunk.content)
        
        # Create metadata object
        metadata = ChunkMetadata(
            source_file=doc_structure.source_path,
            heading_hierarchy=heading_hierarchy,
            section_level=section_level,
            contains_code=contains_code,
            code_languages=code_languages,
            chunk_index=chunk.chunk_index,
            line_start=chunk.line_start,
            line_end=chunk.line_end,
            char_count=char_count,
            token_count=None  # Can be calculated later if needed
        )
        
        return metadata
    
    def build_heading_hierarchy(self, chunk: DocumentChunk) -> List[str]:
        """
        Build full heading path (H1 > H2 > H3).
        
        Traverses the heading parent chain to build the complete hierarchy.
        
        Args:
            chunk: Document chunk
            
        Returns:
            List of heading texts from root to current level
        """
        hierarchy = []
        current_heading = chunk.section.heading
        
        # Traverse up the parent chain
        while current_heading is not None:
            hierarchy.insert(0, current_heading.text)
            current_heading = current_heading.parent
        
        return hierarchy
    
    def detect_code_language(self, code_block: CodeBlock) -> str:
        """
        Detect programming language in code block.
        
        Uses the explicitly specified language if available, otherwise
        attempts heuristic detection based on code patterns.
        
        Args:
            code_block: Code block to analyze
            
        Returns:
            Language identifier string (e.g., "python", "dml", "unknown")
        """
        # First, check if language is explicitly specified
        if code_block.language and code_block.language.strip() and code_block.language != "unknown":
            return code_block.language.lower().strip()
        
        # If no language specified, try heuristic detection
        return self._detect_language_heuristic(code_block.content)
    
    def _detect_language_heuristic(self, code: str) -> str:
        """
        Detect language using pattern matching heuristics.
        
        Args:
            code: Code content to analyze
            
        Returns:
            Detected language or "unknown"
        """
        # Score each language based on pattern matches
        language_scores = {}
        
        for language, patterns in self.language_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
                score += len(matches)
            
            if score > 0:
                language_scores[language] = score
        
        # Return language with highest score
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1])
            return best_language[0]
        
        return "unknown"
    
    def extract_all_code_languages(self, doc_structure: DocumentStructure) -> Set[str]:
        """
        Extract all unique code languages from a document.
        
        Utility method for analyzing document-level language usage.
        
        Args:
            doc_structure: Document structure to analyze
            
        Returns:
            Set of language identifiers found in the document
        """
        languages = set()
        
        for code_block in doc_structure.code_blocks:
            language = self.detect_code_language(code_block)
            if language != "unknown":
                languages.add(language)
        
        return languages
    
    def calculate_token_count(self, text: str, encoding: str = "cl100k_base") -> int:
        """
        Calculate token count for text using tiktoken.
        
        This is an optional method that can be used to populate the
        token_count field in ChunkMetadata.
        
        Args:
            text: Text to tokenize
            encoding: Tiktoken encoding to use
            
        Returns:
            Number of tokens
            
        Raises:
            ImportError: If tiktoken is not installed
        """
        try:
            import tiktoken
            tokenizer = tiktoken.get_encoding(encoding)
            return len(tokenizer.encode(text))
        except ImportError:
            raise ImportError(
                "tiktoken is required for token counting. "
                "Install it with: pip install tiktoken"
            )
