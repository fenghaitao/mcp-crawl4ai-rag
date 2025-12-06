# Database Backend Configuration

The CLI supports multiple database backends for storing and querying embeddings and documentation chunks.

## Available Backends

### 1. Supabase (PostgreSQL + pgvector)
**Best for:** Production deployments, team collaboration, cloud hosting

**Features:**
- Full PostgreSQL database with pgvector extension
- Row-level security (RLS)
- Real-time subscriptions
- Cloud-hosted or self-hosted
- Relational data support

**Setup:**
```bash
# Set in .env
DB_BACKEND=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### 2. ChromaDB
**Best for:** Local development, quick prototyping, no-setup testing

**Features:**
- Zero-setup local vector database
- Built specifically for embeddings and RAG
- Persistent storage to disk
- Metadata filtering
- Multiple distance metrics (cosine, L2, IP)

**Setup:**
```bash
# Set in .env
DB_BACKEND=chroma
CHROMA_DB_PATH=./chroma_db  # Optional, defaults to ./chroma_db

# Or install ChromaDB
pip install chromadb
```

## CLI Usage

### Check Current Backend
```bash
python -m core db backend
```

### Use Specific Backend (Override)
```bash
# Use ChromaDB for this command
python -m core db --backend chroma info

# Use Supabase for this command
python -m core db --backend supabase stats
```

### Database Commands

All database commands support both backends:

```bash
# Get database info
python -m core db info
python -m core db --backend chroma info

# View statistics
python -m core db stats
python -m core db --backend chroma stats

# List records/documents
python -m core db list-all
python -m core db list-all --table crawled_pages --limit 20
python -m core db --backend chroma list-all --table my_collection

# Delete records
python -m core db delete --table crawled_pages
python -m core db --backend chroma delete --table my_collection
```

## Switching Backends

### Method 1: Environment Variable (Persistent)
Edit your `.env` file:
```bash
DB_BACKEND=chroma  # or supabase
```

### Method 2: Command-line Flag (One-time)
```bash
python -m core db --backend chroma info
```

## Backend Comparison

| Feature | Supabase | ChromaDB |
|---------|----------|----------|
| Setup Required | ✅ Yes (cloud account or local install) | ❌ No (just pip install) |
| Storage | Cloud/Self-hosted PostgreSQL | Local file system |
| Vector Search | pgvector extension | Native |
| Relational Queries | ✅ Full SQL support | ❌ Limited |
| Metadata Filtering | ✅ SQL WHERE clauses | ✅ Native support |
| Multi-user | ✅ Yes | ❌ Single process |
| Cost | Free tier + paid plans | Free (local) |
| Best For | Production, teams | Development, testing |

## Migration Between Backends

Currently, there is no automatic migration tool. To switch backends:

1. Export data from current backend
2. Change `DB_BACKEND` in `.env`
3. Import data to new backend

Migration tools are planned for future releases.

## Troubleshooting

### ChromaDB Issues
```bash
# Install ChromaDB if missing
pip install chromadb

# Check if path exists
python -m core db backend

# Create directory manually if needed
mkdir -p ./chroma_db
```

### Supabase Issues
```bash
# Verify credentials
python -m core db backend

# Test connection
python -m core db info
```

## Development

When developing locally, ChromaDB is recommended for:
- Quick iteration
- No network dependency
- No cloud costs
- Simple setup

Switch to Supabase when you need:
- Production deployment
- Team collaboration
- Advanced SQL queries
- Cloud hosting
