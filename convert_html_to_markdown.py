#!/usr/bin/env python3
"""
Convert HTML files to Markdown using the Unstructured library.

This script processes all HTML files in a directory and converts them to Markdown format.
The Unstructured library parses HTML into semantic elements (titles, paragraphs, lists, etc.)
which can then be converted to clean Markdown text.

Requirements:
    pip install unstructured

Usage:
    python convert_html_to_markdown.py <input_dir> [output_dir]
    
Example:
    python convert_html_to_markdown.py ./html_files ./markdown_files
"""

import sys
import os
from pathlib import Path
from typing import List
import argparse

# Import from unstructured library
try:
    from unstructured.partition.html import partition_html
    from unstructured.documents.elements import Element, Title, NarrativeText, ListItem, Table
except ImportError:
    print("Error: unstructured library not found.")
    print("Please install it with: pip install unstructured")
    sys.exit(1)


def element_to_markdown(element: Element) -> str:
    """
    Convert an Unstructured element to Markdown format.
    
    Args:
        element: An element from the unstructured library
        
    Returns:
        Markdown-formatted string
    """
    text = str(element)
    
    # Get element type
    element_type = element.__class__.__name__
    
    # Convert based on element type
    if element_type == "Title":
        # Determine heading level from metadata if available
        level = 1
        if hasattr(element, 'metadata') and element.metadata:
            # Try to infer level from category or other metadata
            category = getattr(element.metadata, 'category', None)
            if category:
                # Map categories to heading levels
                if 'h1' in category.lower():
                    level = 1
                elif 'h2' in category.lower():
                    level = 2
                elif 'h3' in category.lower():
                    level = 3
                elif 'h4' in category.lower():
                    level = 4
                elif 'h5' in category.lower():
                    level = 5
                elif 'h6' in category.lower():
                    level = 6
        
        return f"{'#' * level} {text}\n\n"
    
    elif element_type == "ListItem":
        return f"- {text}\n"
    
    elif element_type == "Table":
        # Tables are already in text format, just add spacing
        return f"\n{text}\n\n"
    
    elif element_type == "NarrativeText":
        return f"{text}\n\n"
    
    elif element_type == "Text":
        return f"{text}\n\n"
    
    else:
        # Default: just return the text with spacing
        return f"{text}\n\n"


def convert_html_to_markdown(html_path: str, output_path: str = None) -> str:
    """
    Convert a single HTML file to Markdown.
    
    Args:
        html_path: Path to the HTML file
        output_path: Optional path to save the Markdown file
        
    Returns:
        Markdown content as string
    """
    print(f"Processing: {html_path}")
    
    try:
        # Partition the HTML file into elements
        elements = partition_html(filename=html_path)
        
        # Convert elements to Markdown
        markdown_lines = []
        for element in elements:
            markdown_lines.append(element_to_markdown(element))
        
        markdown_content = "".join(markdown_lines)
        
        # Save to file if output path is provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"  ✓ Saved to: {output_path}")
        
        return markdown_content
        
    except Exception as e:
        print(f"  ✗ Error processing {html_path}: {e}")
        return ""


def convert_directory(input_dir: str, output_dir: str = None, recursive: bool = True):
    """
    Convert all HTML files in a directory to Markdown.
    
    Args:
        input_dir: Directory containing HTML files
        output_dir: Directory to save Markdown files (default: input_dir + '_markdown')
        recursive: Whether to process subdirectories
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return
    
    # Set default output directory
    if output_dir is None:
        output_dir = str(input_path) + "_markdown"
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all HTML files
    if recursive:
        html_files = list(input_path.rglob("*.html")) + list(input_path.rglob("*.htm"))
    else:
        html_files = list(input_path.glob("*.html")) + list(input_path.glob("*.htm"))
    
    if not html_files:
        print(f"No HTML files found in '{input_dir}'")
        return
    
    print(f"Found {len(html_files)} HTML file(s)")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    # Process each HTML file
    success_count = 0
    failed_count = 0
    
    for html_file in html_files:
        # Calculate relative path to maintain directory structure
        rel_path = html_file.relative_to(input_path)
        
        # Change extension to .md
        md_filename = rel_path.with_suffix('.md')
        md_path = output_path / md_filename
        
        # Convert
        result = convert_html_to_markdown(str(html_file), str(md_path))
        
        if result:
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("-" * 60)
    print(f"Conversion complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(html_files)}")


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Convert HTML files to Markdown using Unstructured library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all HTML files in a directory
  python convert_html_to_markdown.py ./html_files
  
  # Specify output directory
  python convert_html_to_markdown.py ./html_files ./markdown_output
  
  # Convert single file
  python convert_html_to_markdown.py ./example.html ./example.md
  
  # Non-recursive (only top-level files)
  python convert_html_to_markdown.py ./html_files --no-recursive
        """
    )
    
    parser.add_argument(
        'input',
        help='Input HTML file or directory'
    )
    
    parser.add_argument(
        'output',
        nargs='?',
        default=None,
        help='Output Markdown file or directory (optional)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not process subdirectories'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # Check if input is a file or directory
    if input_path.is_file():
        # Single file conversion
        if args.output:
            output_file = args.output
        else:
            output_file = str(input_path.with_suffix('.md'))
        
        convert_html_to_markdown(str(input_path), output_file)
        
    elif input_path.is_dir():
        # Directory conversion
        convert_directory(
            str(input_path),
            args.output,
            recursive=not args.no_recursive
        )
    else:
        print(f"Error: '{args.input}' is not a valid file or directory")
        sys.exit(1)


if __name__ == "__main__":
    main()
