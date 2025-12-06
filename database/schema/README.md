# Database Schema

This directory contains the database schema definitions for the RAG system.

## Tables Overview

### Core Tables

1. **`sources`** - High-level source collections (e.g., simics-dml, simics-python)
2. **`files`** - Individual files with metadata and content hashing 
3. **`content_chunks`** - Text chunks with embeddings and file references

### Table Relationships

```
sources (1) ──→ (many) files
files (1) ──→ (many) content_chunks
```

## Schema Files

- `001_files_table.sql` - Creates the files tracking table
- `002_content_chunks.sql` - Creates the content chunks table with file references

## Content Types

The system supports three content types:
- `code_dml` - DML source code files
- `python_test` - Python test files  
- `documentation` - Documentation files (markdown, HTML, etc.)

## Key Features

### File Tracking
- **Content hashing** for change detection
- **Word counts** and **chunk counts** per file
- **File metadata** (size, modification time, etc.)

### Performance Optimization
- **Partial indexes** for each content type
- **Foreign key relationships** with cascade deletes
- **Unique constraints** to prevent duplicate chunks

### Data Integrity
- **Check constraints** for valid content types
- **Foreign key constraints** for referential integrity
- **Unique constraints** for file paths and chunk numbering

## Usage

Apply schema files in order:
1. Apply `001_files_table.sql` (requires existing `sources` table)
2. Apply `002_content_chunks.sql`

**Note**: These are clean schema files without migration support. Apply to a fresh database or after clearing existing tables.

The schema supports the CLI commands:
- `ingest-dml`, `ingest-python-test`, `ingest-doc` 
- `egest-dml`, `egest-python-test`, `egest-doc`
- File-based operations with change detection and force re-processing