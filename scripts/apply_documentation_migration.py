#!/usr/bin/env python3
"""
Apply database migration to add documentation support fields.

This script adds:
- content_type field to distinguish code from documentation
- heading_hierarchy field for hierarchical retrieval
- Appropriate indexes for efficient querying
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import get_supabase_client


def apply_migration():
    """Apply the documentation fields migration."""
    print("=" * 60)
    print("Applying Documentation Fields Migration")
    print("=" * 60)
    
    # Read migration SQL
    migration_file = Path(__file__).parent.parent / "supabase" / "migrations" / "001_add_documentation_fields.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    print(f"Reading migration from: {migration_file}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Get Supabase client
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Execute migration
    print("\nExecuting migration...")
    print("-" * 60)
    
    try:
        # Split SQL into individual statements
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            # Skip comments
            if statement.startswith('--'):
                continue
            
            print(f"\nExecuting statement {i}/{len(statements)}...")
            
            # Execute via RPC or direct SQL execution
            # Note: Supabase Python client doesn't directly support raw SQL
            # We need to use the PostgREST API or execute via psycopg2
            
            # For now, print instructions for manual execution
            print(f"Statement: {statement[:100]}...")
        
        print("\n" + "=" * 60)
        print("⚠️  MANUAL MIGRATION REQUIRED")
        print("=" * 60)
        print("\nThe Supabase Python client doesn't support raw SQL execution.")
        print("Please apply the migration manually using one of these methods:")
        print("\n1. Via Supabase Dashboard:")
        print("   - Go to your Supabase project dashboard")
        print("   - Navigate to SQL Editor")
        print(f"   - Copy and paste the contents of: {migration_file}")
        print("   - Click 'Run'")
        print("\n2. Via psql command line:")
        print(f"   psql $DATABASE_URL < {migration_file}")
        print("\n3. Via Supabase CLI:")
        print(f"   supabase db push")
        print("\n" + "=" * 60)
        
        # Verify if fields exist (read-only check)
        print("\nVerifying current schema...")
        try:
            # Try to query with new fields
            result = client.table("crawled_pages").select("content_type, heading_hierarchy").limit(1).execute()
            print("✅ Fields already exist! Migration may have been applied previously.")
        except Exception as e:
            print(f"⚠️  Fields not found: {e}")
            print("Please apply the migration as described above.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    apply_migration()
