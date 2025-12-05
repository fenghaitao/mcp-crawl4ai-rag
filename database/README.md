# Database Components

This directory contains all database-related files including schemas, migrations, and SQL scripts.

## 📁 Directory Structure

### `/migrations/` - Database Migrations
Version-controlled database schema changes:
- Supabase migration files
- Schema evolution scripts
- Data migration procedures

### `/sql/` - SQL Scripts & Queries
Utility SQL scripts and queries:
- `add_source_entries.sql` - Add new data sources
- `crawled_pages.sql` - Page crawling queries
- `delete_source_data.sql` - Data cleanup scripts
- `delete_source_data_function.sql` - Cleanup functions

### `/schema/` - Database Schema Documentation
Schema definitions and documentation:
- Table definitions
- Relationship diagrams
- Index specifications
- Constraint documentation

## 🗄️ Database Setup

### Initial Setup
1. Set up Supabase project
2. Configure connection in `.env` file
3. Run initial migrations
4. Execute setup scripts

### Migration Management
```bash
# Apply all migrations
python scripts/apply_all_migrations.py

# Apply documentation-specific migrations
python scripts/apply_documentation_migration.py
```

## 📊 Key Tables & Functions

### Core Tables
- **documents**: Stored document content and metadata
- **chunks**: Processed document chunks with embeddings
- **sources**: Data source configuration and tracking
- **embeddings**: Vector embeddings for semantic search

### Utility Functions
- **delete_source_data()**: Clean up data for specific sources
- **add_source_entries()**: Batch add new source entries
- **search functions**: Vector similarity search operations

## 🔧 Maintenance Scripts

Located in `/sql/` directory:
- Data cleanup and maintenance
- Performance optimization queries  
- Bulk operations
- Diagnostic and monitoring queries

## 📝 Schema Documentation

For detailed schema information, refer to:
- Migration files in `/migrations/`
- Schema documentation (when available in `/schema/`)
- Source code table definitions in `src/`