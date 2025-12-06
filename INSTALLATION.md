# Installation Guide

## Database Backend Options

### Supabase (Default - Production)
The default backend requires no additional installation - all dependencies are included.

```bash
# Works out of the box
python -m core db info
```

### ChromaDB (Local Development)
ChromaDB is now included as a required dependency:

```bash
# ChromaDB is automatically installed
pip install -e .

# Use ChromaDB backend
export DB_BACKEND=chroma
python -m core db info

# Or via backend commands
python -m core db backend info -b chroma
```

### Development Tools (Optional)
To install development tools (linting, formatting):

```bash
pip install -e ".[dev]"
```

## Environment Configuration

Copy and configure your environment:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### Supabase Configuration
```bash
DB_BACKEND=supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
```

### ChromaDB Configuration  
```bash
DB_BACKEND=chroma
CHROMA_DB_PATH=./chroma_db
```

## CLI Usage

```bash
# Check system status
python -m core status
python -m core config

# Database operations
python -m core db info
python -m core db list-all
python -m core db stats

# Backend-specific operations
python -m core db backend info -b supabase
python -m core db backend stats -b chroma
python -m core db backend test -b supabase

# RAG operations
python -m core rag crawl
python -m core rag query "your question"

# Development tools
python -m core dev validate
python -m core dev debug-embeddings
```