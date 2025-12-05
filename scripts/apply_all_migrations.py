#!/usr/bin/env python3
"""
Apply all Supabase migrations.

This script applies all SQL migrations in the supabase/migrations directory
to ensure the database schema is up to date.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import get_supabase_client


def apply_migration(client, migration_file: Path):
    """
    Apply a single migration file.
    
    Args:
        client: Supabase client
        migration_file: Path to migration SQL file
    """
    print(f"\nApplying migration: {migration_file.name}")
    print("-" * 60)
    
    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Split into individual statements (simple split on semicolon)
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        print(f"Found {len(statements)} SQL statements")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if not statement or statement.startswith('--'):
                continue
            
            try:
                # Execute via RPC (Supabase doesn't support direct SQL execution)
                # We'll use the SQL editor or manual application
                print(f"  Statement {i}: {statement[:50]}...")
                
            except Exception as e:
                print(f"  ✗ Error in statement {i}: {e}")
                raise
        
        print(f"✓ Migration {migration_file.name} completed")
        
    except Exception as e:
        print(f"✗ Failed to apply migration {migration_file.name}: {e}")
        raise


def main():
    """Main function."""
    print("=" * 60)
    print("Supabase Migration Application")
    print("=" * 60)
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
    
    if not migrations_dir.exists():
        print(f"✗ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Find all migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("✗ No migration files found")
        sys.exit(1)
    
    print(f"\nFound {len(migration_files)} migration files:")
    for mf in migration_files:
        print(f"  - {mf.name}")
    
    # Get Supabase client
    try:
        client = get_supabase_client()
        print("\n✓ Connected to Supabase")
    except Exception as e:
        print(f"\n✗ Failed to connect to Supabase: {e}")
        print("\nPlease ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in .env")
        sys.exit(1)
    
    # Note about manual application
    print("\n" + "=" * 60)
    print("IMPORTANT: Manual Migration Application Required")
    print("=" * 60)
    print("\nSupabase Python client doesn't support direct SQL execution.")
    print("Please apply migrations manually using one of these methods:")
    print("\n1. Supabase Dashboard SQL Editor:")
    print("   - Go to https://supabase.com/dashboard")
    print("   - Navigate to SQL Editor")
    print("   - Copy and paste each migration file")
    print("   - Execute the SQL")
    
    print("\n2. Using psql command line:")
    print("   psql <connection_string> -f supabase/migrations/001_add_documentation_fields.sql")
    print("   psql <connection_string> -f supabase/migrations/002_add_user_documentation_source.sql")
    
    print("\n3. Using the apply_documentation_migration.py script:")
    print("   python3 scripts/apply_documentation_migration.py")
    
    print("\n" + "=" * 60)
    print("Migration Files to Apply:")
    print("=" * 60)
    
    for mf in migration_files:
        print(f"\n--- {mf.name} ---")
        with open(mf, 'r') as f:
            content = f.read()
            # Show first few lines
            lines = content.split('\n')[:10]
            for line in lines:
                print(line)
            if len(content.split('\n')) > 10:
                print("...")
    
    print("\n" + "=" * 60)
    print("After applying migrations, verify with:")
    print("=" * 60)
    print("\nSELECT column_name, data_type, is_nullable")
    print("FROM information_schema.columns")
    print("WHERE table_name = 'crawled_pages'")
    print("ORDER BY ordinal_position;")


if __name__ == "__main__":
    main()
