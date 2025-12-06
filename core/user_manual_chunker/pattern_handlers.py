"""
Pattern handlers for special documentation structures.

Handles detection and preservation of:
- Lists (ordered and unordered, nested)
- API documentation patterns
- Grammar specifications
- Definition lists
- Tables
- Cross-references
"""

import re
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from .data_models import Paragraph, CodeBlock


@dataclass
class ListItem:
    """Represents a list item with its content and nesting level."""
    content: str
    level: int  # Indentation level (0 = top level)
    line_start: int
    line_end: int
    is_ordered: bool
    parent_context: Optional[str] = None  # Text before the list


@dataclass
class APIDocPattern:
    """Represents an API documentation pattern (function signature + description)."""
    signature: str
    description: str
    line_start: int
    line_end: int
    language: str = "text"


@dataclass
class GrammarRule:
    """Represents a grammar rule with examples."""
    rule: str
    examples: List[str]
    line_start: int
    line_end: int


@dataclass
class DefinitionItem:
    """Represents a term and its definition."""
    term: str
    definition: str
    line_start: int
    line_end: int


@dataclass
class TableStructure:
    """Represents a table structure."""
    content: str  # Full table as text
    line_start: int
    line_end: int
    format_type: str  # "markdown" or "html"


@dataclass
class CrossReference:
    """Represents a cross-reference link."""
    text: str
    target: str
    line_number: int


class ListContextPreserver:
    """Handles detection and preservation of list structures."""
    
    # Patterns for list detection
    UNORDERED_LIST_PATTERN = re.compile(r'^(\s*)([-*+])\s+(.+)$', re.MULTILINE)
    ORDERED_LIST_PATTERN = re.compile(r'^(\s*)(\d+\.)\s+(.+)$', re.MULTILINE)
    
    @staticmethod
    def detect_lists(content: str) -> List[ListItem]:
        """
        Detect list items in content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of ListItem objects
        """
        list_items = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            # Check for unordered list
            unordered_match = re.match(r'^(\s*)([-*+])\s+(.+)$', line)
            if unordered_match:
                indent = unordered_match.group(1)
                level = len(indent) // 2  # Assume 2 spaces per level
                content_text = unordered_match.group(3)
                
                list_items.append(ListItem(
                    content=content_text,
                    level=level,
                    line_start=line_num,
                    line_end=line_num,
                    is_ordered=False
                ))
                continue
            
            # Check for ordered list
            ordered_match = re.match(r'^(\s*)(\d+\.)\s+(.+)$', line)
            if ordered_match:
                indent = ordered_match.group(1)
                level = len(indent) // 2
                content_text = ordered_match.group(3)
                
                list_items.append(ListItem(
                    content=content_text,
                    level=level,
                    line_start=line_num,
                    line_end=line_num,
                    is_ordered=True
                ))
        
        return list_items
    
    @staticmethod
    def should_keep_list_together(list_items: List[ListItem], max_size: int) -> bool:
        """
        Determine if a list should be kept together.
        
        Args:
            list_items: List items to evaluate
            max_size: Maximum chunk size
            
        Returns:
            True if list should be kept together
        """
        if not list_items:
            return False
        
        # Calculate total size of list
        total_size = sum(len(item.content) for item in list_items)
        
        # Keep together if under max size
        return total_size < max_size
    
    @staticmethod
    def extract_parent_context(content: str, list_start_line: int) -> Optional[str]:
        """
        Extract the paragraph immediately before a list.
        
        Args:
            content: Full document content
            list_start_line: Line where list starts
            
        Returns:
            Parent context text or None
        """
        lines = content.split('\n')
        
        if list_start_line <= 1:
            return None
        
        # Look backwards for non-empty lines
        context_lines = []
        for i in range(list_start_line - 2, -1, -1):
            line = lines[i].strip()
            
            # Stop at empty line or heading
            if not line or line.startswith('#'):
                break
            
            context_lines.insert(0, lines[i])
        
        if context_lines:
            return '\n'.join(context_lines).strip()
        
        return None


class APIDocumentationHandler:
    """Handles detection and preservation of API documentation patterns."""
    
    # Pattern for function signatures
    FUNCTION_SIGNATURE_PATTERNS = [
        # C-style: return_type function_name(params)
        re.compile(r'^(\w+(?:\s+\w+)*)\s+(\w+)\s*\(([^)]*)\)\s*$', re.MULTILINE),
        # Python-style: def function_name(params):
        re.compile(r'^def\s+(\w+)\s*\(([^)]*)\)\s*:', re.MULTILINE),
        # Method signature: method_name(params) -> return_type
        re.compile(r'^(\w+)\s*\(([^)]*)\)\s*->\s*(\w+)', re.MULTILINE),
    ]
    
    @staticmethod
    def detect_api_patterns(paragraphs: List[Paragraph], code_blocks: List[CodeBlock]) -> List[APIDocPattern]:
        """
        Detect API documentation patterns.
        
        Looks for patterns like:
        - Function signature followed by description
        - Code block with function followed by explanation
        
        Args:
            paragraphs: List of paragraphs
            code_blocks: List of code blocks
            
        Returns:
            List of APIDocPattern objects
        """
        api_patterns = []
        
        # Check each code block for function signatures
        for cb in code_blocks:
            # Check if code block contains a function signature
            for pattern in APIDocumentationHandler.FUNCTION_SIGNATURE_PATTERNS:
                if pattern.search(cb.content):
                    # This looks like a function signature
                    # Find the description (preceding or following text)
                    description = cb.preceding_text or ""
                    
                    api_patterns.append(APIDocPattern(
                        signature=cb.content,
                        description=description,
                        line_start=cb.line_start,
                        line_end=cb.line_end,
                        language=cb.language
                    ))
                    break
        
        return api_patterns
    
    @staticmethod
    def should_keep_api_doc_together(api_pattern: APIDocPattern, max_size: int) -> bool:
        """
        Determine if API documentation should be kept together.
        
        Args:
            api_pattern: API documentation pattern
            max_size: Maximum chunk size
            
        Returns:
            True if should be kept together
        """
        total_size = len(api_pattern.signature) + len(api_pattern.description)
        return total_size < max_size


class GrammarSpecificationHandler:
    """Handles detection and preservation of grammar specifications."""
    
    # Pattern for grammar rules (BNF-style)
    GRAMMAR_RULE_PATTERN = re.compile(
        r'^([A-Z][A-Za-z_]*)\s*::=\s*(.+)$',
        re.MULTILINE
    )
    
    @staticmethod
    def detect_grammar_rules(content: str) -> List[GrammarRule]:
        """
        Detect grammar rules with examples.
        
        Looks for patterns like:
        - BNF notation: Rule ::= definition
        - EBNF notation: Rule = definition
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of GrammarRule objects
        """
        grammar_rules = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for grammar rule
            match = GrammarSpecificationHandler.GRAMMAR_RULE_PATTERN.match(line)
            if match:
                rule_name = match.group(1)
                rule_def = match.group(2)
                
                # Look for examples in following lines
                examples = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    
                    # Stop at empty line or next rule
                    if not next_line or GrammarSpecificationHandler.GRAMMAR_RULE_PATTERN.match(next_line):
                        break
                    
                    # Check if this looks like an example (indented or starts with "Example:")
                    if next_line.startswith('  ') or next_line.lower().startswith('example'):
                        examples.append(next_line)
                    
                    j += 1
                
                grammar_rules.append(GrammarRule(
                    rule=f"{rule_name} ::= {rule_def}",
                    examples=examples,
                    line_start=i + 1,
                    line_end=j
                ))
                
                i = j
            else:
                i += 1
        
        return grammar_rules
    
    @staticmethod
    def should_keep_grammar_together(grammar_rule: GrammarRule, max_size: int) -> bool:
        """
        Determine if grammar rule should be kept with examples.
        
        Args:
            grammar_rule: Grammar rule with examples
            max_size: Maximum chunk size
            
        Returns:
            True if should be kept together
        """
        total_size = len(grammar_rule.rule) + sum(len(ex) for ex in grammar_rule.examples)
        return total_size < max_size


class DefinitionListHandler:
    """Handles detection and preservation of definition lists."""
    
    # Patterns for definition lists
    MARKDOWN_DEF_PATTERN = re.compile(
        r'^([^:\n]+)\s*:\s*(.+)$',
        re.MULTILINE
    )
    
    @staticmethod
    def detect_definition_lists(content: str) -> List[DefinitionItem]:
        """
        Detect definition lists in various formats.
        
        Formats supported:
        - Markdown: Term: Definition
        - HTML: <dt>Term</dt><dd>Definition</dd>
        - Plain: Term - Definition
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of DefinitionItem objects
        """
        definitions = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            # Check for "Term: Definition" format
            colon_match = re.match(r'^([^:\n]+)\s*:\s*(.+)$', line)
            if colon_match:
                term = colon_match.group(1).strip()
                definition = colon_match.group(2).strip()
                
                # Only treat as definition if term is short (< 50 chars)
                if len(term) < 50 and not term.startswith('#'):
                    definitions.append(DefinitionItem(
                        term=term,
                        definition=definition,
                        line_start=line_num,
                        line_end=line_num
                    ))
                continue
            
            # Check for "Term - Definition" format
            dash_match = re.match(r'^([^-\n]+)\s*-\s*(.+)$', line)
            if dash_match:
                term = dash_match.group(1).strip()
                definition = dash_match.group(2).strip()
                
                # Only treat as definition if term is short
                if len(term) < 50 and not term.startswith('#') and not line.strip().startswith('-'):
                    definitions.append(DefinitionItem(
                        term=term,
                        definition=definition,
                        line_start=line_num,
                        line_end=line_num
                    ))
        
        return definitions
    
    @staticmethod
    def should_keep_definition_together(definition: DefinitionItem, max_size: int) -> bool:
        """
        Determine if definition should be kept with term.
        
        Args:
            definition: Definition item
            max_size: Maximum chunk size
            
        Returns:
            True if should be kept together
        """
        total_size = len(definition.term) + len(definition.definition)
        return total_size < max_size


class TablePreserver:
    """Handles detection and preservation of table structures."""
    
    # Markdown table pattern
    MARKDOWN_TABLE_PATTERN = re.compile(
        r'^\|.+\|$\n^\|[-:\s|]+\|$\n(?:^\|.+\|$\n?)+',
        re.MULTILINE
    )
    
    @staticmethod
    def detect_tables(content: str) -> List[TableStructure]:
        """
        Detect tables in markdown and HTML formats.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of TableStructure objects
        """
        tables = []
        
        # Detect markdown tables
        for match in TablePreserver.MARKDOWN_TABLE_PATTERN.finditer(content):
            table_content = match.group(0)
            line_start = content[:match.start()].count('\n') + 1
            line_end = content[:match.end()].count('\n') + 1
            
            tables.append(TableStructure(
                content=table_content,
                line_start=line_start,
                line_end=line_end,
                format_type="markdown"
            ))
        
        # Detect HTML tables (simple pattern)
        html_table_pattern = re.compile(
            r'<table[^>]*>.*?</table>',
            re.DOTALL | re.IGNORECASE
        )
        
        for match in html_table_pattern.finditer(content):
            table_content = match.group(0)
            line_start = content[:match.start()].count('\n') + 1
            line_end = content[:match.end()].count('\n') + 1
            
            tables.append(TableStructure(
                content=table_content,
                line_start=line_start,
                line_end=line_end,
                format_type="html"
            ))
        
        return tables
    
    @staticmethod
    def should_keep_table_together(table: TableStructure, max_size: int) -> bool:
        """
        Determine if table should be kept together.
        
        Args:
            table: Table structure
            max_size: Maximum chunk size
            
        Returns:
            True if should be kept together
        """
        return len(table.content) < max_size


class CrossReferencePreserver:
    """Handles detection and preservation of cross-references."""
    
    # Markdown link pattern: [text](url)
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    # HTML link pattern: <a href="url">text</a>
    HTML_LINK_PATTERN = re.compile(r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', re.IGNORECASE)
    
    @staticmethod
    def detect_cross_references(content: str) -> List[CrossReference]:
        """
        Detect cross-references (links) in content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of CrossReference objects
        """
        references = []
        lines = content.split('\n')
        
        # Detect markdown links
        for line_num, line in enumerate(lines, start=1):
            for match in CrossReferencePreserver.MARKDOWN_LINK_PATTERN.finditer(line):
                text = match.group(1)
                target = match.group(2)
                
                references.append(CrossReference(
                    text=text,
                    target=target,
                    line_number=line_num
                ))
            
            # Detect HTML links
            for match in CrossReferencePreserver.HTML_LINK_PATTERN.finditer(line):
                target = match.group(1)
                text = match.group(2)
                
                references.append(CrossReference(
                    text=text,
                    target=target,
                    line_number=line_num
                ))
        
        return references
    
    @staticmethod
    def preserve_references_in_chunk(chunk_content: str) -> str:
        """
        Ensure cross-references are preserved in chunk.
        
        This is a no-op since references are already in the text,
        but could be extended to resolve relative links, etc.
        
        Args:
            chunk_content: Chunk text content
            
        Returns:
            Chunk content with preserved references
        """
        # References are already preserved in the text
        # This method exists for future enhancements like:
        # - Resolving relative links
        # - Adding footnotes for external links
        # - Validating link targets
        return chunk_content


class PatternAwareChunker:
    """
    Wrapper that makes chunking decisions aware of special patterns.
    
    This class coordinates all pattern handlers to ensure special
    structures are preserved during chunking.
    """
    
    def __init__(self):
        """Initialize pattern handlers."""
        self.list_handler = ListContextPreserver()
        self.api_handler = APIDocumentationHandler()
        self.grammar_handler = GrammarSpecificationHandler()
        self.definition_handler = DefinitionListHandler()
        self.table_handler = TablePreserver()
        self.reference_handler = CrossReferencePreserver()
    
    def analyze_content(self, content: str, paragraphs: List[Paragraph], 
                       code_blocks: List[CodeBlock]) -> Dict[str, List]:
        """
        Analyze content for all special patterns.
        
        Args:
            content: Full text content
            paragraphs: List of paragraphs
            code_blocks: List of code blocks
            
        Returns:
            Dictionary mapping pattern type to detected patterns
        """
        return {
            'lists': self.list_handler.detect_lists(content),
            'api_docs': self.api_handler.detect_api_patterns(paragraphs, code_blocks),
            'grammar_rules': self.grammar_handler.detect_grammar_rules(content),
            'definitions': self.definition_handler.detect_definition_lists(content),
            'tables': self.table_handler.detect_tables(content),
            'references': self.reference_handler.detect_cross_references(content)
        }
    
    def should_keep_together(self, line_start: int, line_end: int, 
                            patterns: Dict[str, List], max_size: int) -> bool:
        """
        Determine if a range of lines contains patterns that should be kept together.
        
        Args:
            line_start: Start line of range
            line_end: End line of range
            patterns: Detected patterns from analyze_content
            max_size: Maximum chunk size
            
        Returns:
            True if range should be kept together
        """
        # Check if range contains a list
        for list_item in patterns.get('lists', []):
            if line_start <= list_item.line_start <= line_end:
                # Find all list items in this range
                list_group = [li for li in patterns['lists'] 
                             if line_start <= li.line_start <= line_end]
                if self.list_handler.should_keep_list_together(list_group, max_size):
                    return True
        
        # Check if range contains API documentation
        for api_doc in patterns.get('api_docs', []):
            if line_start <= api_doc.line_start <= line_end:
                if self.api_handler.should_keep_api_doc_together(api_doc, max_size):
                    return True
        
        # Check if range contains grammar rules
        for grammar in patterns.get('grammar_rules', []):
            if line_start <= grammar.line_start <= line_end:
                if self.grammar_handler.should_keep_grammar_together(grammar, max_size):
                    return True
        
        # Check if range contains definitions
        for definition in patterns.get('definitions', []):
            if line_start <= definition.line_start <= line_end:
                if self.definition_handler.should_keep_definition_together(definition, max_size):
                    return True
        
        # Check if range contains tables
        for table in patterns.get('tables', []):
            if line_start <= table.line_start <= line_end:
                if self.table_handler.should_keep_table_together(table, max_size):
                    return True
        
        return False
