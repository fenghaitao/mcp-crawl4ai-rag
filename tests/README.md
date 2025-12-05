# Test Suite Organization

This directory contains all test files organized by type and scope.

## 📁 Directory Structure

### `/unit/` - Unit Tests
Component-level tests that test individual functions and classes in isolation:
- `test_semantic_chunker_*.py` - Semantic chunking logic tests
- `test_pattern_handlers.py` - Pattern detection and handling tests  
- `test_metadata_*.py` - Metadata extraction and processing tests
- `test_embedding_generator.py` - Embedding generation tests
- `test_summary_generator.py` - Summary generation tests
- `test_orchestrator.py` - Orchestrator component tests
- `test_error_handling.py` - Error handling and edge case tests
- `test_*_dml_*.py` - DML-specific functionality tests

### `/integration/` - Integration Tests
End-to-end tests that verify component interactions:
- `test_*integration*.py` - Cross-component integration tests
- `test_requirements_validation.py` - System requirements validation
- `test_astchunk_integration.py` - AST chunking integration tests

### `/fixtures/` - Test Data & Fixtures
Reusable test data, sample documents, and test fixtures:
- Sample documents (markdown, HTML, DML files)
- Expected output files
- Mock data for testing
- Configuration files for tests

## 🧪 Running Tests

### Run All Tests
```bash
# Run the entire test suite
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/
```

### Run Specific Test Categories
```bash
# Run only unit tests
python -m pytest tests/unit/

# Run only integration tests
python -m pytest tests/integration/

# Run specific component tests
python -m pytest tests/unit/test_semantic_chunker_*.py
```

### Run Individual Test Files
```bash
# Run specific test file
python -m pytest tests/unit/test_pattern_handlers.py

# Run specific test with verbose output
python -m pytest tests/unit/test_embedding_generator.py -v
```

## 📋 Test Categories by Component

### Chunking System Tests
- `test_semantic_chunker_basic.py`
- `test_semantic_chunker_comprehensive.py`
- `test_pattern_aware_semantic_chunker.py`
- `test_pattern_handlers.py`
- `test_pattern_integration.py`

### Data Processing Tests
- `test_metadata_extractor.py`
- `test_metadata_edge_cases.py`
- `test_metadata_integration.py`
- `test_embedding_generator.py`
- `test_summary_generator.py`

### Integration & Workflow Tests
- `test_orchestrator.py`
- `test_orchestrator_integration.py`
- `test_integration.py`
- `test_astchunk_integration.py`

### Specialized Tests
- `test_dml_parser.py` - DML language parsing
- `test_code_summarization.py` - Code summarization features
- `test_file_type_selection.py` - File type detection
- `test_progress_tracker.py` - Progress tracking functionality

## 🔧 Test Configuration

### Environment Setup
Tests use the same configuration as the main application but may override certain settings for testing purposes.

### Test Data
Test fixtures and sample data should be placed in `/fixtures/` directory and reused across tests when possible.

### Mocking
Tests use appropriate mocking for external dependencies (APIs, databases, file systems) to ensure reliable and fast test execution.

## 📝 Writing New Tests

When adding new tests:
1. Place unit tests in `/unit/` directory
2. Place integration tests in `/integration/` directory
3. Use descriptive test function names
4. Include docstrings explaining what the test verifies
5. Use appropriate fixtures from `/fixtures/` directory
6. Mock external dependencies appropriately
7. Follow existing test patterns and conventions