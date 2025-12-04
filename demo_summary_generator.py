"""
Demo script for SummaryGenerator.

Demonstrates summary generation for documentation chunks with and without code.
"""

from src.user_manual_chunker.summary_generator import SummaryGenerator
from src.user_manual_chunker.data_models import (
    Section,
    Heading,
    Paragraph,
    CodeBlock,
    ChunkMetadata,
)
from src.user_manual_chunker.interfaces import DocumentChunk


def demo_summary_with_code():
    """Demo summary generation for chunk with code."""
    print("=" * 80)
    print("Demo 1: Summary Generation for Documentation with Code")
    print("=" * 80)
    
    # Create a chunk with code (DML device example)
    heading = Heading(level=2, text="Register Definitions", line_number=10)
    
    paragraphs = [
        Paragraph(
            content="The UART controller provides two main registers for configuration and status monitoring. The control register enables the device and sets the operating mode, while the status register indicates transmission readiness.",
            line_start=11,
            line_end=11
        )
    ]
    
    code_blocks = [
        CodeBlock(
            content="""bank regs {
    register ctrl size 4 @ 0x00 {
        field enable @ [0];
        field mode @ [2:1];
    }
    
    register status size 4 @ 0x04 {
        field tx_ready @ [0];
        field rx_ready @ [1];
    }
}""",
            language="dml",
            line_start=13,
            line_end=22
        )
    ]
    
    section = Section(
        heading=heading,
        paragraphs=paragraphs,
        code_blocks=code_blocks
    )
    
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=5,
        line_start=10,
        line_end=22
    )
    
    metadata = ChunkMetadata(
        source_file="simics_dml_uart_controller.md",
        heading_hierarchy=["Device Models", "UART Controller", "Register Definitions"],
        section_level=3,
        contains_code=True,
        code_languages=["dml"],
        chunk_index=5,
        line_start=10,
        line_end=22,
        char_count=len(chunk.content)
    )
    
    # Generate summary
    generator = SummaryGenerator(max_summary_length=50)
    doc_context = "Simics DML 1.4 Reference Manual - Device Modeling Language"
    
    print("\nChunk Content:")
    print("-" * 80)
    print(chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content)
    print("-" * 80)
    
    print("\nMetadata:")
    print(f"  Source: {metadata.source_file}")
    print(f"  Hierarchy: {' > '.join(metadata.heading_hierarchy)}")
    print(f"  Contains Code: {metadata.contains_code}")
    print(f"  Languages: {', '.join(metadata.code_languages)}")
    
    print("\nGenerating Summary...")
    summary = generator.generate_summary(chunk, doc_context, metadata)
    
    print(f"\n✓ Generated Summary:")
    print(f"  {summary}")
    print(f"\n  Length: {len(summary.split())} words")
    print()


def demo_summary_without_code():
    """Demo summary generation for chunk without code."""
    print("=" * 80)
    print("Demo 2: Summary Generation for Documentation without Code")
    print("=" * 80)
    
    # Create a chunk without code (conceptual explanation)
    heading = Heading(level=1, text="Introduction to DML", line_number=1)
    
    paragraphs = [
        Paragraph(
            content="The Device Modeling Language (DML) is a domain-specific language designed for modeling hardware devices in the Simics full-system simulator. DML provides a high-level abstraction for describing device behavior, registers, and interfaces, making it easier to create accurate and maintainable device models.",
            line_start=2,
            line_end=2
        ),
        Paragraph(
            content="DML models are compiled into C code that integrates with the Simics simulation framework. The language includes features for defining memory-mapped registers, implementing device methods, handling events, and managing device state.",
            line_start=4,
            line_end=4
        )
    ]
    
    section = Section(
        heading=heading,
        paragraphs=paragraphs,
        code_blocks=[]
    )
    
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=0,
        line_start=1,
        line_end=4
    )
    
    metadata = ChunkMetadata(
        source_file="simics_dml_introduction.md",
        heading_hierarchy=["Introduction to DML"],
        section_level=1,
        contains_code=False,
        code_languages=[],
        chunk_index=0,
        line_start=1,
        line_end=4,
        char_count=len(chunk.content)
    )
    
    # Generate summary
    generator = SummaryGenerator(max_summary_length=40)
    doc_context = "Simics DML 1.4 Reference Manual"
    
    print("\nChunk Content:")
    print("-" * 80)
    print(chunk.content[:300] + "..." if len(chunk.content) > 300 else chunk.content)
    print("-" * 80)
    
    print("\nMetadata:")
    print(f"  Source: {metadata.source_file}")
    print(f"  Hierarchy: {' > '.join(metadata.heading_hierarchy)}")
    print(f"  Contains Code: {metadata.contains_code}")
    
    print("\nGenerating Summary...")
    summary = generator.generate_summary(chunk, doc_context, metadata)
    
    print(f"\n✓ Generated Summary:")
    print(f"  {summary}")
    print(f"\n  Length: {len(summary.split())} words")
    print()


def demo_summary_api_documentation():
    """Demo summary generation for API documentation."""
    print("=" * 80)
    print("Demo 3: Summary Generation for API Documentation")
    print("=" * 80)
    
    # Create API documentation chunk
    heading = Heading(level=3, text="log.info() Method", line_number=50)
    
    paragraphs = [
        Paragraph(
            content="Logs an informational message to the Simics console. This method is used for general status updates and debugging information during device operation.",
            line_start=51,
            line_end=51
        ),
        Paragraph(
            content="Parameters: message (string) - The message to log",
            line_start=53,
            line_end=53
        ),
        Paragraph(
            content="Returns: None",
            line_start=54,
            line_end=54
        )
    ]
    
    code_blocks = [
        CodeBlock(
            content='log.info("Device initialized successfully");',
            language="dml",
            line_start=56,
            line_end=56
        )
    ]
    
    section = Section(
        heading=heading,
        paragraphs=paragraphs,
        code_blocks=code_blocks
    )
    
    chunk = DocumentChunk(
        content=section.get_text_content(),
        section=section,
        chunk_index=12,
        line_start=50,
        line_end=56
    )
    
    metadata = ChunkMetadata(
        source_file="simics_dml_api_reference.md",
        heading_hierarchy=["API Reference", "Logging", "log.info() Method"],
        section_level=3,
        contains_code=True,
        code_languages=["dml"],
        chunk_index=12,
        line_start=50,
        line_end=56,
        char_count=len(chunk.content)
    )
    
    # Generate summary
    generator = SummaryGenerator(max_summary_length=35)
    doc_context = "Simics DML API Reference"
    
    print("\nChunk Content:")
    print("-" * 80)
    print(chunk.content)
    print("-" * 80)
    
    print("\nMetadata:")
    print(f"  Source: {metadata.source_file}")
    print(f"  Hierarchy: {' > '.join(metadata.heading_hierarchy)}")
    print(f"  Contains Code: {metadata.contains_code}")
    
    print("\nGenerating Summary...")
    summary = generator.generate_summary(chunk, doc_context, metadata)
    
    print(f"\n✓ Generated Summary:")
    print(f"  {summary}")
    print(f"\n  Length: {len(summary.split())} words")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "SUMMARY GENERATOR DEMO" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    demo_summary_with_code()
    demo_summary_without_code()
    demo_summary_api_documentation()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  ✓ LLM-based summary generation with documentation-specific prompts")
    print("  ✓ Fallback to extractive summaries on LLM failure")
    print("  ✓ Code mention in summaries when code is present")
    print("  ✓ Document context integration for accurate descriptions")
    print("  ✓ Configurable summary length limits")
    print()


if __name__ == "__main__":
    main()
