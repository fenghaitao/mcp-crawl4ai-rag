# Scripts Usage Guide

This directory contains a comprehensive set of scripts for crawling and processing web content for RAG (Retrieval Augmented Generation) systems. This guide explains how to use each script and the complete pipeline.

## 🚀 Quick Start: Complete Pipeline

The easiest way to crawl content is using the automated pipeline:

```bash
.venv/bin/python scripts/crawl_pipeline.py "https://intel.github.io/simics/docs/dml-1.4-reference-manual/"
```

This single command will:
1. Extract all URLs from the site
2. Download pages locally (static HTML)
3. Clean your database
4. Crawl the local files and populate your RAG database

## 📋 Complete Pipeline Script

### `crawl_pipeline.py` - Master Automation Script

**Purpose:** Automates the entire crawling process from URL extraction to database population.

**Usage:**
```bash
.venv/bin/python scripts/crawl_pipeline.py <input_url> [options]
```

**Parameters:**
- `input_url` - Initial URL to extract links from (sitemap, index page, etc.)
- `--output-dir`, `-o` - Directory for all outputs (default: `./pipeline_output`)
- `--skip-cleanup` - Skip database cleanup step
- `--skip-extraction` - Skip URL extraction (use existing files)
- `--skip-download` - Skip page download (use existing files)
- `--max-urls` - Maximum number of URLs to process

**Examples:**
```bash
# Full pipeline with default settings
.venv/bin/python scripts/crawl_pipeline.py "https://example.com/sitemap.xml"

# Custom output directory and URL limit
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --output-dir ./my_crawl \
  --max-urls 100

# Skip cleanup (keep existing database data)
.venv/bin/python scripts/crawl_pipeline.py \
  "https://example.com/" \
  --skip-cleanup

# Rerun only crawling (skip extraction and download)
.venv/bin/python scripts/crawl_pipeline.py \
  "https://example.com/" \
  --skip-extraction \
  --skip-download
```

**Output Files:**
- `extracted_urls.json` - All URLs found on the site
- `downloaded_pages/` - Directory with static HTML files
- `local_urls.json` - file:// URLs for local crawling

## 🔧 Individual Scripts

### `delete_all_records.py` - Database Cleanup

**Purpose:** Removes all data from crawled_pages, sources, and code_examples tables.

**Usage:**
```bash
.venv/bin/python scripts/delete_all_records.py [--confirm]
```

**Parameters:**
- `--confirm` - Auto-confirm deletion (for automation)

**Interactive Mode:**
```bash
.venv/bin/python scripts/delete_all_records.py
# Will prompt: Type 'DELETE ALL' to confirm
```

**Automated Mode:**
```bash
.venv/bin/python scripts/delete_all_records.py --confirm
# Deletes without prompting (used by pipeline)
```

### `extract_simics_urls.py` - URL Extraction

**Purpose:** Extracts all URLs from a website, sitemap, or documentation site.

**Usage:**
```bash
.venv/bin/python scripts/extract_simics_urls.py <input_url> [options]
```

**Parameters:**
- `input_url` - URL to extract links from
- `--output` - Output JSON file (default: extracted_urls.json)
- `--max-urls` - Maximum URLs to extract

**Examples:**
```bash
# Extract from sitemap
.venv/bin/python scripts/extract_simics_urls.py \
  "https://example.com/sitemap.xml" \
  --output my_urls.json

# Extract with limit
.venv/bin/python scripts/extract_simics_urls.py \
  "https://docs.example.com/" \
  --max-urls 50
```

### `download_pages_locally.py` - Local Page Download

**Purpose:** Downloads web pages as static HTML files for consistent crawling.

**Usage:**
```bash
.venv/bin/python scripts/download_pages_locally.py <input_json> [options]
```

**Parameters:**
- `input_json` - JSON file containing URLs to download
- `--output-dir`, `-o` - Directory to save files (default: ./downloaded_pages)
- `--output-json`, `-j` - Output JSON with file:// URLs (default: ./local_urls.json)

**Examples:**
```bash
# Basic download
.venv/bin/python scripts/download_pages_locally.py extracted_urls.json

# Custom directories
.venv/bin/python scripts/download_pages_locally.py \
  my_urls.json \
  --output-dir ./static_pages \
  --output-json ./file_urls.json
```

**Benefits of Local Download:**
- **Predictable content sizes** - No server-side processing
- **No JavaScript redirects** - Static HTML only
- **Consistent results** - Files don't change between runs
- **Faster crawling** - No network delays during processing

### `crawl_local_files.py` - Local File Crawling

**Purpose:** Crawls local HTML files and populates the RAG database.

**Usage:**
```bash
.venv/bin/python scripts/crawl_local_files.py <local_urls_json>
```

**Parameters:**
- `local_urls_json` - JSON file with file:// URLs to crawl

**Example:**
```bash
.venv/bin/python scripts/crawl_local_files.py local_urls.json
```

### `simple_crawl_json.py` - Direct Web Crawling

**Purpose:** Directly crawl URLs from the web (alternative to local file approach).

**Usage:**
```bash
.venv/bin/python scripts/simple_crawl_json.py <urls_json> [--static-only]
```

**Parameters:**
- `urls_json` - JSON file containing URLs to crawl
- `--static-only` - Disable JavaScript (override environment setting)

**Examples:**
```bash
# Normal crawling (uses environment CRAWL_STATIC_CONTENT_ONLY setting)
.venv/bin/python scripts/simple_crawl_json.py urls.json

# Force static content only
.venv/bin/python scripts/simple_crawl_json.py urls.json --static-only
```

## ⚙️ Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# Crawling Configuration
CRAWL_STATIC_CONTENT_ONLY=true    # Recommended for most documentation

# Embedding Configuration  
USE_QWEN_EMBEDDINGS=true          # Use local Qwen model (recommended)
USE_COPILOT_EMBEDDINGS=false      # Use GitHub Copilot API
OPENAI_API_KEY=your_key_here      # For OpenAI embeddings

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Optional Features
USE_RERANKING=true                # Enable search result reranking
USE_QWEN_RERANKER=true           # Use local Qwen reranker
USE_KNOWLEDGE_GRAPH=false        # Enable Neo4j integration
```

### Virtual Environment Detection

All scripts automatically detect and use `.venv/bin/python` if available:

```bash
# If .venv exists, scripts use:
.venv/bin/python

# Otherwise, they use:
python
```

## 🎯 Common Workflows

### 1. First-Time Setup

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 2. Run complete pipeline
.venv/bin/python scripts/crawl_pipeline.py "https://docs.example.com/"

# 3. Verify in database
# Your RAG system now has clean, local content
```

### 2. Update Existing Content

```bash
# Clean database and re-crawl
.venv/bin/python scripts/crawl_pipeline.py "https://docs.example.com/"

# Or keep existing data and add new
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --skip-cleanup
```

### 3. Partial Updates

```bash
# Re-crawl existing downloaded files (if you changed embedding settings)
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --skip-extraction \
  --skip-download

# Re-download and crawl (if website content changed)
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --skip-extraction
```

### 4. Testing Different Settings

```bash
# Test with different embedding models
# 1. Change .env: USE_QWEN_EMBEDDINGS=false, USE_COPILOT_EMBEDDINGS=true
# 2. Re-crawl existing files
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --skip-extraction \
  --skip-download
```

## 📊 Understanding Output

### Content Size Analysis

When you see output like:
```
📄 Raw content length: 1160968 characters
📦 Split into 233 chunks (target: ~5000 chars per chunk)
```

This means:
- **1,160,968 characters** = ~1.16MB of text content
- **233 chunks** = 1,160,968 ÷ 5,000 ≈ 232 pieces
- Each chunk becomes a separate database record for RAG

### Local vs Web Crawling Comparison

**Local File Crawling Benefits:**
- **Predictable sizes** - HTML file size = crawled content size
- **No JavaScript surprises** - Static content only
- **Faster processing** - No network delays
- **Reproducible results** - Same content every time

**Web Crawling Characteristics:**
- **Dynamic content** - May include JavaScript-loaded content
- **Potential redirects** - May crawl more than expected
- **Variable results** - Content may change between runs
- **Network dependent** - Slower due to HTTP requests

## 🐛 Troubleshooting

### Common Issues

**"Body tag not found" errors:**
- Fixed in current version with `wait_for="css:body"`
- Ensures page loads completely before processing

**Huge content sizes:**
- Use local file approach for predictable sizes
- Check if JavaScript redirects are causing issues
- Set `CRAWL_STATIC_CONTENT_ONLY=true`

**Database connection errors:**
- Verify `.env` file has correct Supabase credentials
- Check network connectivity
- Ensure Supabase project is active

**Virtual environment not detected:**
- Ensure `.venv/bin/python` exists
- Scripts fall back to system Python automatically

### Performance Tips

**For Large Sites:**
- Use `--max-urls` to limit initial crawling
- Use local file approach for consistent performance
- Enable batching in environment variables

**For Embedding Performance:**
- Use `USE_QWEN_EMBEDDINGS=true` for local processing
- Use `USE_COPILOT_EMBEDDINGS=true` for cloud processing
- Avoid mixing embedding types in same database

## 📈 Best Practices

### 1. Always Use Local File Approach for Documentation

```bash
# Recommended for documentation sites
.venv/bin/python scripts/crawl_pipeline.py "https://docs.example.com/"
```

Benefits:
- Predictable content sizes
- No server-side processing surprises
- Faster subsequent processing
- Reproducible results

### 2. Clean Database When Changing Embedding Models

```bash
# When switching from OpenAI to Qwen embeddings:
# 1. Update .env file
# 2. Clean and re-crawl
.venv/bin/python scripts/crawl_pipeline.py "https://docs.example.com/"
```

### 3. Use Skip Options for Development

```bash
# During development, skip slow steps:
.venv/bin/python scripts/crawl_pipeline.py \
  "https://docs.example.com/" \
  --skip-extraction \
  --skip-download
```

### 4. Monitor Content Sizes

Watch the output for unexpected content sizes:
- **Small sites**: 10-100 chunks per page
- **Documentation pages**: 100-500 chunks per page  
- **Very large**: 1000+ chunks may indicate redirects

## 🔗 Integration with MCP Server

After running the pipeline, your MCP server will have clean content available for RAG queries:

```python
# In your MCP client
crawl_result = perform_rag_query("How do I use DML templates?")
# Returns relevant chunks from your crawled documentation
```

The pipeline ensures your RAG system has:
- ✅ Clean, consistent content
- ✅ Proper chunking for retrieval
- ✅ Quality embeddings for search
- ✅ Organized source tracking

---

**Happy Crawling! 🚀**

For more information, see the main project README.md or check individual script help:
```bash
.venv/bin/python scripts/crawl_pipeline.py --help
```