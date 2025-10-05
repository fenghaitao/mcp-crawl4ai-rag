# Tests for crawl4ai-mcp

This directory contains integration tests for the crawl4ai-mcp project, including tests for Neo4j knowledge graph functionality and GitHub Copilot integration.

## Test Files

### Core Integration Tests

- **`test_neo4j_integration.py`** - Tests Neo4j connection, knowledge graph tools, and repository parsing
- **`test_copilot_integration.py`** - Tests GitHub Copilot embeddings and chat completions
- **`run_all_tests.py`** - Test runner that executes all integration tests

### Sample Files

- **`sample_code_for_validation.py`** - Sample Python code for testing hallucination detection

## Prerequisites

Before running tests, ensure you have the following configured:

### Required Environment Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
USE_KNOWLEDGE_GRAPH=true

# AI Provider Configuration (choose one or both)
# For GitHub Copilot
GITHUB_TOKEN=your_github_token
USE_COPILOT_EMBEDDINGS=true
USE_COPILOT_CHAT=true

# For OpenAI (fallback or primary)
OPENAI_API_KEY=your_openai_api_key
USE_COPILOT_EMBEDDINGS=false
USE_COPILOT_CHAT=false
```

### System Requirements

- Neo4j database running on localhost:7687
- GitHub Copilot subscription (for Copilot tests)
- OpenAI API key (for fallback or primary usage)
- Python 3.12+ with required dependencies installed

## Running Tests

### Run All Tests

The test runner automatically loads environment variables from `.env` file:

```bash
# From project root - automatically loads .env file
.venv/bin/python tests/run_all_tests.py

# Override specific variables if needed
GITHUB_TOKEN=your_token .venv/bin/python tests/run_all_tests.py
```

### Run Individual Test Suites

Individual test files also automatically load `.env` when run directly:

```bash
# Neo4j integration tests (auto-loads .env)
.venv/bin/python tests/test_neo4j_integration.py

# GitHub Copilot integration tests (auto-loads .env)
.venv/bin/python tests/test_copilot_integration.py
```

### Run with pytest

```bash
# Install pytest if not already installed
.venv/bin/pip install pytest pytest-asyncio

# Run all tests
.venv/bin/python -m pytest tests/ -v

# Run specific test
.venv/bin/python -m pytest tests/test_neo4j_integration.py -v

# Run integration tests only
.venv/bin/python -m pytest tests/ -v -m integration
```

## Test Coverage

### Neo4j Integration Tests

- ✅ **Connection Test** - Verifies Neo4j database connectivity
- ✅ **Module Import Test** - Ensures all knowledge graph modules load correctly
- ✅ **Repository Parsing Test** - Tests DirectNeo4jExtractor functionality
- ✅ **Query Operations Test** - Validates database read/write operations
- ✅ **Sample Code Generation** - Creates test files for hallucination detection

### GitHub Copilot Integration Tests

- ✅ **Embedding Tests** - Single and batch embedding generation
- ✅ **Chat Completion Tests** - GPT-4o chat model integration
- ✅ **Utils Integration** - Tests unified embedding/chat functions
- ✅ **Fallback Behavior** - Ensures OpenAI fallback works when Copilot unavailable

## Expected Output

### Successful Test Run

```
🚀 crawl4ai-mcp Integration Test Suite
============================================================
Environment Configuration Check
============================================================
Environment Variables:
  ✅ NEO4J_URI: bolt://localhost:7687
  ✅ NEO4J_USER: neo4j
  ✅ NEO4J_PASSWORD: ********
  ✅ USE_KNOWLEDGE_GRAPH: true
  ✅ GITHUB_TOKEN: ********
  ✅ USE_COPILOT_EMBEDDINGS: true
  ✅ USE_COPILOT_CHAT: true

✅ All critical configurations present

============================================================
Running Neo4j Integration Tests
============================================================
Testing Neo4j connection...
✅ Neo4j connection successful!
✅ Neo4j Version: 2025.09.0
...
🎉 All Neo4j integration tests passed!

============================================================
Running GitHub Copilot Integration Tests
============================================================
Testing GitHub Copilot Embedding Client...
✅ Copilot client initialized successfully
...
🎉 All Copilot integration tests passed!

============================================================
TEST SUMMARY
============================================================
Neo4j Integration: ✅ PASSED
GitHub Copilot Integration: ✅ PASSED

Results: 2/2 test suites passed
🎉 All integration tests passed!
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Ensure Neo4j is running on localhost:7687
   - Check NEO4J_PASSWORD is correct
   - Verify NEO4J_USER (usually 'neo4j')

2. **Copilot Tests Skipped**
   - Set GITHUB_TOKEN environment variable
   - Ensure you have an active GitHub Copilot subscription
   - Check token has appropriate permissions

3. **Import Errors**
   - Run tests from project root directory
   - Ensure virtual environment is activated
   - Install missing dependencies with `uv pip install -e .`

### Debug Mode

To get more detailed output, run individual test files directly:

```bash
.venv/bin/python tests/test_neo4j_integration.py
.venv/bin/python tests/test_copilot_integration.py
```

## Contributing

When adding new tests:

1. Follow the existing naming convention: `test_*.py`
2. Include both unit tests and integration tests
3. Add appropriate pytest markers (`@pytest.mark.integration`)
4. Update this README with new test descriptions
5. Ensure tests can be run both individually and via the test runner

## Integration with CI/CD

These tests are designed to work in CI/CD environments. Set the required environment variables in your CI configuration and run:

```bash
.venv/bin/python tests/run_all_tests.py
```

The test runner exits with code 0 on success and 1 on failure, making it suitable for automated testing pipelines.