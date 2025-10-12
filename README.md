<h1 align="center">Crawl4AI RAG MCP Server</h1>

<p align="center">
  <em>Web Crawling and RAG Capabilities for AI Agents and AI Coding Assistants</em>
</p>

A powerful implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) integrated with [Crawl4AI](https://crawl4ai.com) and [Supabase](https://supabase.com/) for providing AI agents and AI coding assistants with advanced web crawling and RAG capabilities.

With this MCP server, you can <b>scrape anything</b> and then <b>use that knowledge anywhere</b> for RAG.

The primary goal is to bring this MCP server into [Archon](https://github.com/coleam00/Archon) as I evolve it to be more of a knowledge engine for AI coding assistants to build AI agents. This first version of the Crawl4AI/RAG MCP server will be improved upon greatly soon, especially making it more configurable so you can use different embedding models and run everything locally with Ollama.

Consider this GitHub repository a testbed, hence why I haven't been super actively address issues and pull requests yet. I certainly will though as I bring this into Archon V2!

## Overview

This MCP server provides tools that enable AI agents to crawl websites, store content in a vector database (Supabase), and perform RAG over the crawled content. It follows the best practices for building MCP servers based on the [Mem0 MCP server template](https://github.com/coleam00/mcp-mem0/) I provided on my channel previously.

The server includes several advanced RAG strategies that can be enabled to enhance retrieval quality:
- **Contextual Embeddings** for enriched semantic understanding
- **Hybrid Search** combining vector and keyword search
- **Agentic RAG** for specialized code example extraction
- **Reranking** for improved result relevance using cross-encoder models
- **Knowledge Graph** for AI hallucination detection and repository code analysis

See the [Configuration section](#configuration) below for details on how to enable and configure these strategies.

## Vision

The Crawl4AI RAG MCP server is just the beginning. Here's where we're headed:

1. **Integration with Archon**: Building this system directly into [Archon](https://github.com/coleam00/Archon) to create a comprehensive knowledge engine for AI coding assistants to build better AI agents.

2. **Multiple Embedding Models**: Expanding beyond OpenAI to support a variety of embedding models, including the ability to run everything locally with Ollama for complete control and privacy.

3. **Advanced RAG Strategies**: Implementing sophisticated retrieval techniques like contextual retrieval, late chunking, and others to move beyond basic "naive lookups" and significantly enhance the power and precision of the RAG system, especially as it integrates with Archon.

4. **Enhanced Chunking Strategy**: Implementing a Context 7-inspired chunking approach that focuses on examples and creates distinct, semantically meaningful sections for each chunk, improving retrieval precision.

5. **Performance Optimization**: Increasing crawling and indexing speed to make it more realistic to "quickly" index new documentation to then leverage it within the same prompt in an AI coding assistant.

## Features

- **Smart URL Detection**: Automatically detects and handles different URL types (regular webpages, sitemaps, text files)
- **Recursive Crawling**: Follows internal links to discover content
- **Parallel Processing**: Efficiently crawls multiple pages simultaneously
- **Content Chunking**: Intelligently splits content by headers and size for better processing
- **Vector Search**: Performs RAG over crawled content, optionally filtering by data source for precision
- **Source Retrieval**: Retrieve sources available for filtering to guide the RAG process

## Tools

The server provides essential web crawling and search tools:

### Core Tools (Always Available)

1. **`crawl_single_page`**: Quickly crawl a single web page and store its content in the vector database
   - **`disable_javascript`**: Optional parameter to disable JavaScript for static content only (prevents redirects)
2. **`smart_crawl_url`**: Intelligently crawl a full website based on the type of URL provided (sitemap, llms-full.txt, or a regular webpage that needs to be crawled recursively)
   - **`disable_javascript`**: Optional parameter (currently only shows warning; use `crawl_single_page` for static content)
3. **`get_available_sources`**: Get a list of all available sources (domains) in the database
4. **`perform_rag_query`**: Search for relevant content using semantic search with optional source filtering

### Conditional Tools

5. **`search_code_examples`** (requires `USE_AGENTIC_RAG=true`): Search specifically for code examples and their summaries from crawled documentation. This tool provides targeted code snippet retrieval for AI coding assistants.

### Knowledge Graph Tools (requires `USE_KNOWLEDGE_GRAPH=true`, see below)

6. **`parse_github_repository`**: Parse a GitHub repository into a Neo4j knowledge graph, extracting classes, methods, functions, and their relationships for hallucination detection
7. **`check_ai_script_hallucinations`**: Analyze Python scripts for AI hallucinations by validating imports, method calls, and class usage against the knowledge graph
8. **`query_knowledge_graph`**: Explore and query the Neo4j knowledge graph with commands like `repos`, `classes`, `methods`, and custom Cypher queries

## Prerequisites

- [Docker/Docker Desktop](https://www.docker.com/products/docker-desktop/) if running the MCP server as a container (recommended)
- [Python 3.12+](https://www.python.org/downloads/) if running the MCP server directly through uv
  - **Note**: For machines without sudo permissions, see the installation script option in the [Using uv directly](#using-uv-directly-no-docker) section
- [Supabase](https://supabase.com/) (database for RAG)
- **Embeddings** (choose one):
  - [OpenAI API key](https://platform.openai.com/api-keys) (for OpenAI text-embedding-3-small)
  - [GitHub Copilot subscription](https://github.com/features/copilot) + [GitHub token](https://github.com/settings/tokens) (for GitHub Copilot embeddings)
- [Neo4j](https://neo4j.com/) (optional, for knowledge graph functionality) - see [Knowledge Graph Setup](#knowledge-graph-setup) section

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/coleam00/mcp-crawl4ai-rag.git
   cd mcp-crawl4ai-rag
   ```

2. Build the Docker image:
   ```bash
   docker build -t mcp/crawl4ai-rag --build-arg PORT=8051 .
   ```

3. Create a `.env` file based on the configuration section below

### Using uv directly (no Docker)

1. Clone this repository:
   ```bash
   git clone https://github.com/coleam00/mcp-crawl4ai-rag.git
   cd mcp-crawl4ai-rag
   ```

2. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

3. Create and activate a virtual environment:
   ```bash
   uv venv
   .venv\Scripts\activate
   # on Mac/Linux: source .venv/bin/activate
   ```

4. Install dependencies:
   
   **Option A: With sudo permissions (recommended)**
   ```bash
   uv pip install -e .
   # To avoid downloading large NVIDIA CUDA packages (4GB+), use:
   # uv pip install --torch-backend cpu -e .
   crawl4ai-setup
   ```
   
   **Option B: Without sudo permissions (for restricted environments)**
   
   If you're on a machine where you don't have sudo access (e.g., shared servers, HPC clusters), use the provided installation script:
   ```bash
   .venv/bin/python install_deps.py
   ```
   
   This script will:
   - Install all Python dependencies using `uv pip`
   - Install Playwright browsers (Chromium, FFMPEG)
   - Run the crawl4ai setup automatically
   
   ⚠️ **Note**: System-level dependencies for Playwright are not installed without sudo. If you encounter browser-related issues, you may need to request your system administrator to run:
   ```bash
   sudo .venv/bin/python -m playwright install-deps chromium
   ```

5. Create a `.env` file based on the configuration section below

## Database Setup

Before running the server, you need to set up the database with the pgvector extension:

1. Go to the SQL Editor in your Supabase dashboard (create a new project first if necessary)

2. Create a new query and paste the contents of `crawled_pages.sql`

3. Run the query to create the necessary tables and functions

## Knowledge Graph Setup (Optional)

To enable AI hallucination detection and repository analysis features, you need to set up Neo4j.

Also, the knowledge graph implementation isn't fully compatible with Docker yet, so I would recommend right now running directly through uv if you want to use the hallucination detection within the MCP server!

For installing Neo4j:

### Local AI Package (Recommended)

The easiest way to get Neo4j running locally is with the [Local AI Package](https://github.com/coleam00/local-ai-packaged) - a curated collection of local AI services including Neo4j:

1. **Clone the Local AI Package**:
   ```bash
   git clone https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Start Neo4j**:
   Follow the instructions in the Local AI Package repository to start Neo4j with Docker Compose

3. **Default connection details**:
   - URI: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: Check the Local AI Package documentation for the default password

### Manual Neo4j Installation

Alternatively, install Neo4j directly:

1. **Install Neo4j Desktop**: Download from [neo4j.com/download](https://neo4j.com/download/)

2. **Create a new database**:
   - Open Neo4j Desktop
   - Create a new project and database
   - Set a password for the `neo4j` user
   - Start the database

3. **Note your connection details**:
   - URI: `bolt://localhost:7687` (default)
   - Username: `neo4j` (default)
   - Password: Whatever you set during creation

## Configuration

Create a `.env` file in the project root with the following variables:

```
# MCP Server Configuration
HOST=0.0.0.0
PORT=8051
TRANSPORT=sse

# AI Provider Configuration
USE_COPILOT_EMBEDDINGS=false
USE_COPILOT_CHAT=false

# OpenAI API Configuration (when USE_COPILOT_EMBEDDINGS=false or USE_COPILOT_CHAT=false)
OPENAI_API_KEY=your_openai_api_key

# GitHub Copilot Configuration (when USE_COPILOT_EMBEDDINGS=true or USE_COPILOT_CHAT=true)
GITHUB_TOKEN=your_github_token

# LLM for summaries and contextual embeddings
MODEL_CHOICE=gpt-4o

# RAG Strategies (set to "true" or "false", default to "false")
USE_CONTEXTUAL_EMBEDDINGS=false
USE_HYBRID_SEARCH=false
USE_AGENTIC_RAG=false
USE_RERANKING=false
USE_KNOWLEDGE_GRAPH=false

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Neo4j Configuration (required for knowledge graph functionality)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

### Embedding Options

The Crawl4AI RAG MCP server supports two embedding providers:

#### **OpenAI Embeddings (Default)**
Uses OpenAI's `text-embedding-3-small` model for generating embeddings.

- **Setup**: Set `USE_COPILOT_EMBEDDINGS=false` and provide your `OPENAI_API_KEY`
- **Cost**: Pay-per-use based on OpenAI's pricing
- **Performance**: Fast and reliable
- **When to use**: When you have an OpenAI API key and want predictable billing

#### **GitHub Copilot Embeddings**
Uses GitHub Copilot's embedding API with the same `text-embedding-3-small` model.

- **Setup**: Set `USE_COPILOT_EMBEDDINGS=true` and provide your `GITHUB_TOKEN`
- **Requirements**: Active GitHub Copilot subscription
- **Cost**: Included with your Copilot subscription (no additional per-embedding charges)
- **Performance**: Fast and reliable, same underlying model as OpenAI
- **When to use**: When you have a Copilot subscription and want to leverage it for embeddings

**Note**: Both options use the same underlying model (`text-embedding-3-small`), so embedding quality and dimensions (1536) are identical. The choice depends on your subscription preferences and billing setup.

### Chat Completion Options

The Crawl4AI RAG MCP server also supports two providers for chat completions (used for contextual embeddings, code summaries, etc.):

#### **OpenAI Chat Completions (Default)**
Uses OpenAI's chat models like `gpt-4o-mini` for generating summaries and contextual information.

- **Setup**: Set `USE_COPILOT_CHAT=false` and provide your `OPENAI_API_KEY`
- **Models**: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`, etc.
- **Cost**: Pay-per-use based on OpenAI's pricing
- **When to use**: When you have an OpenAI API key and want access to the full range of OpenAI models

#### **GitHub Copilot Chat Completions**
Uses GitHub Copilot's chat API with models like `gpt-4o`.

- **Setup**: Set `USE_COPILOT_CHAT=true` and provide your `GITHUB_TOKEN`
- **Models**: Primarily `gpt-4o` (automatically mapped from other model names)
- **Requirements**: Active GitHub Copilot subscription
- **Cost**: Included with your Copilot subscription
- **When to use**: When you have a Copilot subscription and want to leverage it for chat completions

**Recommended Configuration for Full Copilot Usage:**
```
USE_COPILOT_EMBEDDINGS=true
USE_COPILOT_CHAT=true
MODEL_CHOICE=gpt-4o
GITHUB_TOKEN=your_github_token
COPILOT_REQUESTS_PER_MINUTE=60
```

### Rate Limiting & Production Features

The GitHub Copilot integration includes enterprise-grade rate limiting and error handling:

#### **Automatic Rate Limiting**
- **Requests per minute**: Configurable via `COPILOT_REQUESTS_PER_MINUTE` (default: 60)
- **Burst protection**: Max 10 requests per 10 seconds
- **Smart throttling**: Automatically waits when limits approached

#### **Error Handling & Resilience**
- **Exponential backoff**: On 429 rate limit and 5xx server errors
- **Token refresh**: Automatic refresh on 401 authentication errors
- **Retry logic**: Smart retry with rate limiting for failed requests
- **Max backoff**: 30 seconds maximum wait time

#### **Production Ready**
- **Zero downtime**: Seamless token refresh during operation
- **Long-running stability**: Handles extended usage without failure
- **Configurable limits**: Adjust based on your usage patterns
- **Comprehensive logging**: Clear feedback on rate limiting actions

### RAG Strategy Options

The Crawl4AI RAG MCP server supports four powerful RAG strategies that can be enabled independently:

#### 1. **USE_CONTEXTUAL_EMBEDDINGS**
When enabled, this strategy enhances each chunk's embedding with additional context from the entire document. The system passes both the full document and the specific chunk to an LLM (configured via `MODEL_CHOICE`) to generate enriched context that gets embedded alongside the chunk content.

- **When to use**: Enable this when you need high-precision retrieval where context matters, such as technical documentation where terms might have different meanings in different sections.
- **Trade-offs**: Slower indexing due to LLM calls for each chunk, but significantly better retrieval accuracy.
- **Cost**: Additional LLM API calls during indexing.

#### 2. **USE_HYBRID_SEARCH**
Combines traditional keyword search with semantic vector search to provide more comprehensive results. The system performs both searches in parallel and intelligently merges results, prioritizing documents that appear in both result sets.

- **When to use**: Enable this when users might search using specific technical terms, function names, or when exact keyword matches are important alongside semantic understanding.
- **Trade-offs**: Slightly slower search queries but more robust results, especially for technical content.
- **Cost**: No additional API costs, just computational overhead.

#### 3. **USE_AGENTIC_RAG**
Enables specialized code example extraction and storage. When crawling documentation, the system identifies code blocks (≥300 characters), extracts them with surrounding context, generates summaries, and stores them in a separate vector database table specifically designed for code search.

- **When to use**: Essential for AI coding assistants that need to find specific code examples, implementation patterns, or usage examples from documentation.
- **Trade-offs**: Significantly slower crawling due to code extraction and summarization, requires more storage space.
- **Cost**: Additional LLM API calls for summarizing each code example.
- **Benefits**: Provides a dedicated `search_code_examples` tool that AI agents can use to find specific code implementations.

#### 4. **USE_RERANKING**
Applies cross-encoder reranking to search results after initial retrieval. Uses a lightweight cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to score each result against the original query, then reorders results by relevance.

- **When to use**: Enable this when search precision is critical and you need the most relevant results at the top. Particularly useful for complex queries where semantic similarity alone might not capture query intent.
- **Trade-offs**: Adds ~100-200ms to search queries depending on result count, but significantly improves result ordering.
- **Cost**: No additional API costs - uses a local model that runs on CPU.
- **Benefits**: Better result relevance, especially for complex queries. Works with both regular RAG search and code example search.

#### 5. **USE_KNOWLEDGE_GRAPH**
Enables AI hallucination detection and repository analysis using Neo4j knowledge graphs. When enabled, the system can parse GitHub repositories into a graph database and validate AI-generated code against real repository structures. (NOT fully compatible with Docker yet, I'd recommend running through uv)

- **When to use**: Enable this for AI coding assistants that need to validate generated code against real implementations, or when you want to detect when AI models hallucinate non-existent methods, classes, or incorrect usage patterns.
- **Trade-offs**: Requires Neo4j setup and additional dependencies. Repository parsing can be slow for large codebases, and validation requires repositories to be pre-indexed.
- **Cost**: No additional API costs for validation, but requires Neo4j infrastructure (can use free local installation or cloud AuraDB).
- **Benefits**: Provides three powerful tools: `parse_github_repository` for indexing codebases, `check_ai_script_hallucinations` for validating AI-generated code, and `query_knowledge_graph` for exploring indexed repositories.

You can now tell the AI coding assistant to add a Python GitHub repository to the knowledge graph like:

"Add https://github.com/pydantic/pydantic-ai.git to the knowledge graph"

Make sure the repo URL ends with .git.

You can also have the AI coding assistant check for hallucinations with scripts it just created, or you can manually run the command:

```
python knowledge_graphs/ai_hallucination_detector.py [full path to your script to analyze]
```

### Recommended Configurations

**For general documentation RAG:**
```
USE_CONTEXTUAL_EMBEDDINGS=false
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=false
USE_RERANKING=true
```

**For AI coding assistant with code examples:**
```
USE_CONTEXTUAL_EMBEDDINGS=true
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=true
USE_RERANKING=true
USE_KNOWLEDGE_GRAPH=false
```

**For AI coding assistant with hallucination detection:**
```
USE_CONTEXTUAL_EMBEDDINGS=true
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=true
USE_RERANKING=true
USE_KNOWLEDGE_GRAPH=true
```

**For fast, basic RAG:**
```
USE_CONTEXTUAL_EMBEDDINGS=false
USE_HYBRID_SEARCH=true
USE_AGENTIC_RAG=false
USE_RERANKING=false
USE_KNOWLEDGE_GRAPH=false
```

## Running the Server

### Using Docker

```bash
docker run --env-file .env -p 8051:8051 mcp/crawl4ai-rag
```

### Using Python

```bash
uv run src/crawl4ai_mcp.py
```

The server will start and listen on the configured host and port.

### ⏱️ **Important: Wait for Server Ready Message**

**The MCP server takes time to initialize all components before it's ready to accept connections.** You **must** wait for the startup completion message before connecting your MCP client:

```
============================================================
🚀 MCP Crawl4AI RAG Server Initialization Complete!
============================================================

📊 Embedding Provider: Qwen (Local)
🔗 Embedding Model: Qwen/Qwen3-Embedding-0.6B
💬 Chat Model Provider: GitHub Copilot
🤖 Model Choice: gpt-4o-mini
🔍 Reranking Model: Qwen/Qwen3-Reranker-0.6B
🧠 Knowledge Graph: Enabled
🗄️  Supabase: Connected

✅ Server is ready to accept connections!
💡 Connect your MCP client to start using RAG and web crawling tools.
============================================================
```

#### Why Does Startup Take So Long?

The initialization time depends on your configuration, but can take **30 seconds to 2+ minutes** due to:

1. **🤖 Model Downloads**: First-time model downloads can be large:
   - **Qwen3-Embedding-0.6B**: ~1.2GB download
   - **Qwen3-Reranker-0.6B**: ~1.2GB download  
   - **CrossEncoder reranker**: ~100MB download
   - Models are cached after first download

2. **🔧 Model Loading**: Loading models into memory:
   - **Embedding models**: 10-30 seconds to load
   - **Reranking models**: 5-15 seconds to load
   - **CPU optimization**: Models are configured for CPU use

3. **🗄️ Database Connections**: 
   - **Supabase**: Connection verification and setup
   - **Neo4j**: Knowledge graph initialization (if enabled)

4. **🌐 External Service Verification**:
   - **GitHub Copilot**: Token validation and rate limit setup
   - **OpenAI**: API key verification

#### Performance Tips

- **Subsequent startups are faster** once models are cached locally
- **Disable unused features** to reduce startup time:
  ```bash
  USE_RERANKING=false          # Skip reranker model loading
  USE_KNOWLEDGE_GRAPH=false    # Skip Neo4j setup
  USE_QWEN_EMBEDDINGS=false    # Use faster cloud embeddings
  ```
- **Use SSE transport** for better connection reliability during startup

**⚠️ Do not connect your MCP client until you see the "Server is ready to accept connections!" message.**

### 🚫 **JavaScript Redirect Handling**

Some websites use JavaScript redirects that can cause the crawler to extract much more content than expected. For example, a simple documentation page might redirect to load an entire reference manual.

#### **Configuration Options**

**1. Environment Variable (Global Setting):**
```bash
# In your .env file
CRAWL_STATIC_CONTENT_ONLY=true   # All crawling uses static content only (recommended)
CRAWL_STATIC_CONTENT_ONLY=false  # All crawling uses JavaScript for dynamic content
```

**2. Tool Parameter (Per-Request Override):**
```python
# Override environment setting for specific requests
crawl_single_page(url="https://docs.example.com/page.html", disable_javascript=True)
crawl_single_page(url="https://docs.example.com/page.html", disable_javascript=False)

# Use environment setting (None = use DISABLE_JAVASCRIPT from .env)
crawl_single_page(url="https://docs.example.com/page.html")
```

**3. Script Command Line (Override Environment):**
```bash
# Use environment variable setting
python scripts/simple_crawl_json.py urls.json

# Force static content only (overrides environment)
python scripts/simple_crawl_json.py urls.json --static-only
```

#### **When to Use `disable_javascript=True`**

Use JavaScript disabled when you want:
- **Original page content only** (no JavaScript redirects)
- **Static HTML content** without dynamic loading
- **Faster crawling** of simple pages
- **Predictable content size** for large documentation sites

#### **Configuration Precedence**

The system uses this priority order:
1. **Tool parameter** (`disable_javascript=True/False`) - highest priority
2. **Script CLI flag** (`--static-only`) - overrides environment
**3. Environment variable** (`CRAWL_STATIC_CONTENT_ONLY=true`) - default setting
4. **System default** (`false`) - if nothing else is set

**💡 Tip: Try both modes to see which gives you the content you actually need for your RAG system.**

## Integration with MCP Clients

### SSE Configuration

Once you have the server running with SSE transport, you can connect to it using this configuration:

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "transport": "sse",
      "url": "http://localhost:8051/sse"
    }
  }
}
```

> **Note for Windsurf users**: Use `serverUrl` instead of `url` in your configuration:
> ```json
> {
>   "mcpServers": {
>     "crawl4ai-rag": {
>       "transport": "sse",
>       "serverUrl": "http://localhost:8051/sse"
>     }
>   }
> }
> ```
>
> **Note for Docker users**: Use `host.docker.internal` instead of `localhost` if your client is running in a different container. This will apply if you are using this MCP server within n8n!

> **Note for Claude Code users**: 
```
claude mcp add-json crawl4ai-rag '{"type":"http","url":"http://localhost:8051/sse"}' --scope user
```

### Stdio Configuration

Add this server to your MCP configuration for Claude Desktop, Windsurf, or any other MCP client:

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "python",
      "args": ["path/to/crawl4ai-mcp/src/crawl4ai_mcp.py"],
      "env": {
        "TRANSPORT": "stdio",
        "OPENAI_API_KEY": "your_openai_api_key",
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_SERVICE_KEY": "your_supabase_service_key",
        "USE_KNOWLEDGE_GRAPH": "false",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_neo4j_password"
      }
    }
  }
}
```

### Docker with Stdio Configuration

```json
{
  "mcpServers": {
    "crawl4ai-rag": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "-e", "OPENAI_API_KEY", 
               "-e", "SUPABASE_URL", 
               "-e", "SUPABASE_SERVICE_KEY",
               "-e", "USE_KNOWLEDGE_GRAPH",
               "-e", "NEO4J_URI",
               "-e", "NEO4J_USER",
               "-e", "NEO4J_PASSWORD",
               "mcp/crawl4ai"],
      "env": {
        "TRANSPORT": "stdio",
        "OPENAI_API_KEY": "your_openai_api_key",
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_SERVICE_KEY": "your_supabase_service_key",
        "USE_KNOWLEDGE_GRAPH": "false",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_neo4j_password"
      }
    }
  }
}
```

## Knowledge Graph Architecture

The knowledge graph system stores repository code structure in Neo4j with the following components:

### Core Components (`knowledge_graphs/` folder):

- **`parse_repo_into_neo4j.py`**: Clones and analyzes GitHub repositories, extracting Python classes, methods, functions, and imports into Neo4j nodes and relationships
- **`ai_script_analyzer.py`**: Parses Python scripts using AST to extract imports, class instantiations, method calls, and function usage
- **`knowledge_graph_validator.py`**: Validates AI-generated code against the knowledge graph to detect hallucinations (non-existent methods, incorrect parameters, etc.)
- **`hallucination_reporter.py`**: Generates comprehensive reports about detected hallucinations with confidence scores and recommendations
- **`query_knowledge_graph.py`**: Interactive CLI tool for exploring the knowledge graph (functionality now integrated into MCP tools)

### Knowledge Graph Schema:

The Neo4j database stores code structure as:

**Nodes:**
- `Repository`: GitHub repositories
- `File`: Python files within repositories  
- `Class`: Python classes with methods and attributes
- `Method`: Class methods with parameter information
- `Function`: Standalone functions
- `Attribute`: Class attributes

**Relationships:**
- `Repository` -[:CONTAINS]-> `File`
- `File` -[:DEFINES]-> `Class`
- `File` -[:DEFINES]-> `Function`
- `Class` -[:HAS_METHOD]-> `Method`
- `Class` -[:HAS_ATTRIBUTE]-> `Attribute`

### Workflow:

1. **Repository Parsing**: Use `parse_github_repository` tool to clone and analyze open-source repositories
2. **Code Validation**: Use `check_ai_script_hallucinations` tool to validate AI-generated Python scripts
3. **Knowledge Exploration**: Use `query_knowledge_graph` tool to explore available repositories, classes, and methods

## Building Your Own Server

This implementation provides a foundation for building more complex MCP servers with web crawling capabilities. To build your own:

1. Add your own tools by creating methods with the `@mcp.tool()` decorator
2. Create your own lifespan function to add your own dependencies
3. Modify the `utils.py` file for any helper functions you need
4. Extend the crawling capabilities by adding more specialized crawlers

## Troubleshooting

### Installation Issues on Machines Without Sudo

If you're working on a shared server, HPC cluster, or any environment where you don't have sudo/administrator permissions:

1. **Use the provided installation script**:
   ```bash
   .venv/bin/python install_deps.py
   ```
   
   This script handles:
   - Installing all Python dependencies via `uv pip`
   - Installing Playwright browsers (Chromium, FFMPEG, Headless Shell)
   - Running the crawl4ai setup (creates `.crawl4ai` folder, initializes database)

2. **If you encounter browser-related errors**:
   
   The script installs browsers but **skips system-level dependencies** that require sudo. If you see errors like:
   ```
   Error: libgobject-2.0.so.0: cannot open shared object file
   ```
   
   You'll need to:
   - Ask your system administrator to install Playwright dependencies:
     ```bash
     sudo .venv/bin/python -m playwright install-deps chromium
     ```
   - Or use Docker instead (recommended for restricted environments)

3. **Alternative: Use Docker**:
   
   Docker containers have their own isolated environment and don't require sudo on the host machine (only to install Docker itself initially). This is the recommended approach for production deployments and restricted environments.

### Common Issues

- **Memory errors during crawling**: Reduce `max_concurrent` parameter in `smart_crawl_url` (try 5 instead of 10)
- **Rate limiting errors**: Check your API rate limits and adjust `COPILOT_REQUESTS_PER_MINUTE` in `.env`
- **Neo4j connection errors**: Ensure Neo4j is running and the connection details in `.env` are correct
- **Supabase connection errors**: Verify your `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are correct

For more detailed parameter documentation, see `SMART_CRAWL_GUIDE.md`.

## Testing Your RAG System

After crawling content into your database, you can test and verify your RAG system using the included query script.

### Quick RAG Testing with `scripts/query_rag.py`

The `query_rag.py` script provides a command-line interface to test your RAG database and ensure everything is working correctly:

```bash
# Basic search to test your setup
python scripts/query_rag.py "your search query here"

# List all available sources in your database
python scripts/query_rag.py --list-sources

# Search with specific filtering
python scripts/query_rag.py "device implementation" --source-type python --count 5 --verbose
```

**Key Testing Scenarios:**

1. **Test Web Documentation**: Search crawled web docs
   ```bash
   python scripts/query_rag.py "API reference" --source-type docs
   ```

2. **Test Source Code**: Search crawled source files (if using Simics crawling script)
   ```bash
   python scripts/query_rag.py "DML device registers" --source-type dml
   python scripts/query_rag.py "Python device class" --source-type python
   ```

3. **Test Code Examples** (requires `USE_AGENTIC_RAG=true`):
   ```bash
   python scripts/query_rag.py "implementation example" --type both
   ```

4. **Test Advanced Features**:
   ```bash
   # Test hybrid search (vector + keyword)
   python scripts/query_rag.py "specific function name" --hybrid
   
   # Test reranking quality
   python scripts/query_rag.py "complex query" --count 10 --verbose
   ```

**Expected Results:**
- ✅ **Similarity scores** between 0.3-0.8+ (higher = better match)
- ✅ **Rich metadata** showing file paths, methods, classes
- ✅ **Relevant content** matching your search terms
- ✅ **Multiple sources** if you've crawled different sites/codebases

**Troubleshooting:**
- 📭 **No results found**: Check if you've crawled content and your database is populated
- 🔧 **Poor relevance**: Try enabling `USE_RERANKING=true` in your `.env` for better result ordering
- 🐛 **Connection errors**: Verify your Supabase credentials and database setup

See `scripts/README.md` for complete parameter documentation and advanced usage examples.
