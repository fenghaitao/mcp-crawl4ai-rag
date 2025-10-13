# Simics Neo4j Knowledge Graph Integration

This directory contains tools for analyzing Simics Device Modeling Language (DML) code and Python tests into a Neo4j knowledge graph. This extends the existing Neo4j code analysis to support Simics-specific patterns and relationships.

## 🎯 Purpose

Create a comprehensive knowledge graph of Simics codebase that enables:

- **Device Architecture Analysis**: Understand device inheritance hierarchies and interface implementations
- **Test Coverage Tracking**: Identify which devices have test coverage and which don't
- **API Usage Patterns**: Analyze how Simics APIs are used across the codebase
- **Cross-Language Relationships**: Connect DML device definitions to Python test implementations
- **Code Navigation**: Explore dependencies and relationships visually

## 🏗️ Architecture

### Node Types

#### DML (Device Modeling Language)
- **DMLFile**: DML source files
- **DMLDevice**: Device definitions with inheritance
- **DMLInterface**: Interface declarations
- **DMLMethod**: Device method definitions
- **DMLAttribute**: Device attributes
- **DMLRegister**: Memory-mapped registers

#### Python Tests
- **TestFile**: Python test files
- **TestFunction**: Individual test functions
- **TestFixture**: Pytest fixtures
- **SimicsAPI**: Simics API calls
- **DeviceUnderTest**: Devices being tested

#### Regular Python (existing)
- **File**: Python source files
- **Class**: Class definitions
- **Function**: Function definitions
- etc.

### Relationship Types

#### DML Relationships
- **DEFINES**: File defines device/interface
- **INHERITS_FROM**: Device inheritance
- **IMPLEMENTS**: Device implements interface
- **HAS_METHOD**: Device has method
- **HAS_ATTRIBUTE**: Device has attribute
- **HAS_REGISTER**: Device has register

#### Test Relationships
- **CONTAINS**: File contains test/fixture
- **TESTS**: Test function tests device
- **USES_API**: Test uses Simics API
- **USES_FIXTURE**: Test uses fixture

## 📁 Files

### Core Analysis Tools

- **`simics_dml_parser.py`**: DML language parser for extracting device structure
- **`simics_test_analyzer.py`**: Enhanced Python test analyzer for Simics patterns
- **`parse_simics_into_neo4j.py`**: Main analyzer that coordinates DML and test analysis
- **`query_simics_knowledge_graph.py`**: Pre-built queries and interactive interface

### Usage Scripts

- **Analysis**: Use `parse_simics_into_neo4j.py` to populate the graph
- **Querying**: Use `query_simics_knowledge_graph.py` to explore the data

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install Neo4j (Docker recommended)
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest

# Set environment variable
export NEO4J_PASSWORD=password
```

### 2. Analyze Simics Code

```bash
# Analyze entire Simics installation
python parse_simics_into_neo4j.py --local-path /path/to/simics-7-packages-2025-38-linux64/

# Analyze only DML files
python parse_simics_into_neo4j.py --local-path /path/to/simics/ --dml-only

# Analyze only test files
python parse_simics_into_neo4j.py --local-path /path/to/simics/ --tests-only
```

### 3. Query the Graph

```bash
# Get overall statistics
python query_simics_knowledge_graph.py --query stats

# Find untested devices
python query_simics_knowledge_graph.py --query untested-devices

# Show device hierarchy for a specific device
python query_simics_knowledge_graph.py --query device-hierarchy uart_device

# Interactive mode
python query_simics_knowledge_graph.py --interactive
```

## 📊 Pre-built Queries

### Device Analysis

```bash
# Device inheritance hierarchy
--query device-hierarchy [device_name]

# Interface implementations
--query device-interfaces [device_name]

# Device methods and registers
--query device-methods <device_name>
--query device-registers <device_name>

# Find similar devices
--query similar-devices <device_name>

# Device dependencies and relationships
--query device-dependencies <device_name>
```

### Test Coverage

```bash
# Test coverage analysis
--query test-coverage [device_name]

# Find untested devices
--query untested-devices

# Test patterns and categories
--query test-patterns

# Test fixtures
--query test-fixtures
```

### API Usage

```bash
# Simics API usage patterns
--query api-usage [api_name]

# Cross-language connections
--query cross-language-links
```

### Statistics

```bash
# Overall codebase statistics
--query stats
```

## 🔍 Example Queries

### Custom Cypher Queries

```cypher
// Find all UART-related devices
MATCH (d:DMLDevice) 
WHERE d.name =~ '(?i).*uart.*'
RETURN d.name, d.file_path

// Find devices with the most methods
MATCH (d:DMLDevice)-[:HAS_METHOD]->(m:DMLMethod)
RETURN d.name, count(m) as method_count
ORDER BY method_count DESC
LIMIT 10

// Find test functions that use specific APIs
MATCH (t:TestFunction)-[:USES_API]->(api:SimicsAPI)
WHERE api.name CONTAINS 'create_object'
RETURN t.name, t.file_path

// Show inheritance chains
MATCH path = (child:DMLDevice)-[:INHERITS_FROM*]->(root:DMLDevice)
WHERE NOT (root)-[:INHERITS_FROM]->()
RETURN [node in nodes(path) | node.name] as inheritance_chain
ORDER BY length(path) DESC
```

### Interactive Mode Examples

```bash
python query_simics_knowledge_graph.py --interactive

simics-kg> stats
simics-kg> query device-hierarchy uart_device
simics-kg> query untested-devices
simics-kg> custom MATCH (d:DMLDevice) RETURN d.name LIMIT 5
simics-kg> quit
```

## 🎯 Use Cases

### 1. Code Understanding
- **Device Architecture**: Visualize device inheritance and composition
- **Interface Analysis**: Understand which devices implement which interfaces
- **API Patterns**: Learn common Simics API usage patterns

### 2. Development Support
- **Impact Analysis**: "What breaks if I change this device?"
- **Test Discovery**: "Which tests should I run for this change?"
- **Pattern Learning**: "How do similar devices implement this functionality?"

### 3. Quality Assurance
- **Test Coverage**: Identify devices without adequate testing
- **Architecture Review**: Validate design patterns and relationships
- **Dependency Analysis**: Understand component relationships

### 4. Documentation
- **Code Exploration**: Navigate codebase relationships visually
- **Architecture Diagrams**: Generate insights for documentation
- **Learning Paths**: Guide new developers through code structure

## ⚙️ Configuration

### Environment Variables

```bash
export NEO4J_PASSWORD=your_password    # Neo4j password
export NEO4J_URI=bolt://localhost:7687  # Neo4j connection URI (optional)
export NEO4J_USER=neo4j                 # Neo4j username (optional)
```

### Command Line Options

```bash
# Neo4j connection
--neo4j-uri bolt://localhost:7687
--neo4j-user neo4j
--neo4j-password password

# Analysis filters
--dml-only          # Only analyze DML files
--tests-only        # Only analyze test files  
--python-only       # Only analyze regular Python files

# Output options
--format json       # JSON output format
--limit 100        # Limit results
--log-level DEBUG  # Logging level
```

## 🔧 Advanced Usage

### Custom DML Patterns

The DML parser can be extended to recognize additional patterns:

```python
# In simics_dml_parser.py
self.patterns['custom_pattern'] = re.compile(r'your_pattern_here')
```

### Custom Test Analysis

The test analyzer can be enhanced for project-specific patterns:

```python
# In simics_test_analyzer.py
def _extract_custom_patterns(self, tree, content):
    # Add custom test pattern extraction
    pass
```

### Performance Optimization

For large codebases:

```bash
# Process specific subdirectories
python parse_simics_into_neo4j.py --local-path /path/to/simics/devices/

# Use filters to reduce scope
python parse_simics_into_neo4j.py --local-path /path/to/simics/ --dml-only
```

## 🐛 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   ```bash
   # Check Neo4j is running
   docker ps
   # Verify credentials
   export NEO4J_PASSWORD=correct_password
   ```

2. **DML Parsing Errors**
   ```bash
   # Check log output for specific parsing issues
   python parse_simics_into_neo4j.py --local-path /path --log-level DEBUG
   ```

3. **Memory Issues with Large Codebases**
   ```bash
   # Process in smaller chunks
   python parse_simics_into_neo4j.py --local-path /path/to/subset/ --dml-only
   ```

### Performance Tips

- Use `--dml-only` or `--tests-only` for faster analysis
- Process subdirectories separately for very large codebases
- Monitor Neo4j memory usage during large imports

## 🔗 Integration

### With Existing RAG System

This Neo4j integration is designed to **complement** the existing Supabase RAG system:

- **Neo4j**: Code structure, relationships, dependencies
- **Supabase**: Documentation content, semantic search

Both systems can be used together for comprehensive code understanding.

### With Development Workflow

```bash
# Before making changes - understand impact
python query_simics_knowledge_graph.py --query device-dependencies my_device

# After making changes - update graph
python parse_simics_into_neo4j.py --local-path /path/to/changed/files/

# Verify test coverage
python query_simics_knowledge_graph.py --query test-coverage my_device
```

## 📈 Future Enhancements

- **Visual Graph Browser**: Web interface for graph exploration
- **Change Impact Analysis**: Track code changes and their effects
- **Automated Test Generation**: Suggest tests based on device structure
- **Performance Metrics**: Code complexity and coupling analysis
- **Integration with IDEs**: Direct integration with development tools

---

This Simics Neo4j integration provides a powerful foundation for understanding and navigating complex device code, enabling better development decisions and improved code quality.