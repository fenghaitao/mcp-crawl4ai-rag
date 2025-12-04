"""
Test pattern handlers for special documentation structures.
"""

from src.user_manual_chunker.pattern_handlers import (
    ListContextPreserver,
    APIDocumentationHandler,
    GrammarSpecificationHandler,
    DefinitionListHandler,
    TablePreserver,
    CrossReferencePreserver,
    PatternAwareChunker,
)
from src.user_manual_chunker.data_models import Paragraph, CodeBlock


def test_list_detection():
    """Test list detection."""
    content = """
Some intro text.

- First item
- Second item
  - Nested item
  - Another nested
- Third item

More text after.
"""
    
    list_handler = ListContextPreserver()
    lists = list_handler.detect_lists(content)
    
    print(f"✓ Detected {len(lists)} list items")
    assert len(lists) == 5, f"Expected 5 list items, got {len(lists)}"
    assert lists[0].level == 0, "First item should be level 0"
    assert lists[2].level == 1, "Nested item should be level 1"
    print("✓ List detection works correctly")


def test_api_documentation_detection():
    """Test API documentation pattern detection."""
    paragraphs = [
        Paragraph(
            content="This function calculates the sum of two numbers.",
            line_start=1,
            line_end=1
        )
    ]
    
    code_blocks = [
        CodeBlock(
            content="def add(a, b):\n    return a + b",
            language="python",
            line_start=3,
            line_end=4,
            preceding_text="This function calculates the sum of two numbers."
        )
    ]
    
    api_handler = APIDocumentationHandler()
    api_patterns = api_handler.detect_api_patterns(paragraphs, code_blocks)
    
    print(f"✓ Detected {len(api_patterns)} API patterns")
    assert len(api_patterns) == 1, f"Expected 1 API pattern, got {len(api_patterns)}"
    assert "def add" in api_patterns[0].signature
    print("✓ API documentation detection works correctly")


def test_grammar_rule_detection():
    """Test grammar rule detection."""
    content = """
Expression ::= Term ('+' Term)*
  Example: 1 + 2 + 3

Term ::= Factor ('*' Factor)*
  Example: 2 * 3 * 4
"""
    
    grammar_handler = GrammarSpecificationHandler()
    rules = grammar_handler.detect_grammar_rules(content)
    
    print(f"✓ Detected {len(rules)} grammar rules")
    assert len(rules) == 2, f"Expected 2 grammar rules, got {len(rules)}"
    assert "Expression" in rules[0].rule
    assert len(rules[0].examples) > 0, "Should have examples"
    print("✓ Grammar rule detection works correctly")


def test_definition_list_detection():
    """Test definition list detection."""
    content = """
API: Application Programming Interface
SDK: Software Development Kit
IDE: Integrated Development Environment
"""
    
    def_handler = DefinitionListHandler()
    definitions = def_handler.detect_definition_lists(content)
    
    print(f"✓ Detected {len(definitions)} definitions")
    assert len(definitions) == 3, f"Expected 3 definitions, got {len(definitions)}"
    assert definitions[0].term == "API"
    print("✓ Definition list detection works correctly")


def test_table_detection():
    """Test table detection."""
    content = """
| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |
| Value 3  | Value 4  |
"""
    
    table_handler = TablePreserver()
    tables = table_handler.detect_tables(content)
    
    print(f"✓ Detected {len(tables)} tables")
    assert len(tables) == 1, f"Expected 1 table, got {len(tables)}"
    assert tables[0].format_type == "markdown"
    print("✓ Table detection works correctly")


def test_cross_reference_detection():
    """Test cross-reference detection."""
    content = """
See the [documentation](https://example.com/docs) for more info.
Also check <a href="https://example.com">this link</a>.
"""
    
    ref_handler = CrossReferencePreserver()
    references = ref_handler.detect_cross_references(content)
    
    print(f"✓ Detected {len(references)} cross-references")
    assert len(references) == 2, f"Expected 2 references, got {len(references)}"
    assert references[0].text == "documentation"
    print("✓ Cross-reference detection works correctly")


def test_pattern_aware_chunker():
    """Test pattern-aware chunker integration."""
    content = """
# API Reference

The following function adds two numbers:

def add(a, b):
    return a + b

## Parameters

- a: First number
- b: Second number
"""
    
    paragraphs = [
        Paragraph(
            content="The following function adds two numbers:",
            line_start=3,
            line_end=3
        )
    ]
    
    code_blocks = [
        CodeBlock(
            content="def add(a, b):\n    return a + b",
            language="python",
            line_start=5,
            line_end=6,
            preceding_text="The following function adds two numbers:"
        )
    ]
    
    chunker = PatternAwareChunker()
    patterns = chunker.analyze_content(content, paragraphs, code_blocks)
    
    print(f"✓ Analyzed content and found patterns:")
    print(f"  - Lists: {len(patterns['lists'])}")
    print(f"  - API docs: {len(patterns['api_docs'])}")
    print(f"  - Grammar rules: {len(patterns['grammar_rules'])}")
    print(f"  - Definitions: {len(patterns['definitions'])}")
    print(f"  - Tables: {len(patterns['tables'])}")
    print(f"  - References: {len(patterns['references'])}")
    
    assert len(patterns['lists']) > 0, "Should detect list items"
    assert len(patterns['api_docs']) > 0, "Should detect API documentation"
    print("✓ Pattern-aware chunker works correctly")


if __name__ == "__main__":
    print("Testing pattern handlers...\n")
    
    test_list_detection()
    print()
    
    test_api_documentation_detection()
    print()
    
    test_grammar_rule_detection()
    print()
    
    test_definition_list_detection()
    print()
    
    test_table_detection()
    print()
    
    test_cross_reference_detection()
    print()
    
    test_pattern_aware_chunker()
    print()
    
    print("=" * 60)
    print("All pattern handler tests passed! ✓")
    print("=" * 60)
