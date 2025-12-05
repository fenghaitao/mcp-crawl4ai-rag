# Examples and Demos

This directory contains example code, demonstrations, and sample outputs.

## 📁 Directory Structure

### `/demos/` - Demo Scripts
Interactive demonstration scripts showing system capabilities:
- `demo_orchestrator.py` - Complete pipeline demonstration
- `demo_dml_chunking.py` - DML file chunking examples
- `demo_embedding_generator.py` - Embedding generation examples
- `demo_summary_generator.py` - Summary generation examples
- `demo_pattern_aware_chunker.py` - Pattern-aware chunking demonstration
- `demo_pattern_handlers.py` - Pattern detection examples
- `demo_metadata_extractor.py` - Metadata extraction examples
- `demo_error_handling.py` - Error handling scenarios

### `/outputs/` - Demo Output Files
Sample outputs from demo scripts:
- `demo_output_orchestrator.json` - Full pipeline output example
- `demo_output_vector_db.json` - Vector database content example
- Generated embeddings and summaries
- Processed document chunks

### `/notebooks/` - Jupyter Notebooks
Interactive tutorials and exploratory analysis:
- Tutorial notebooks for learning the system
- Exploratory data analysis examples
- Interactive demonstrations of key features

## 🎯 Running Demos

### Prerequisites
Ensure you have:
1. Configured `.env` file with required API keys
2. Installed all dependencies: `pip install -r requirements.txt`
3. Downloaded required models (if using local models)

### Basic Usage Examples

#### Run Complete Pipeline Demo
```bash
python examples/demos/demo_orchestrator.py
```

#### Test DML Chunking
```bash
python examples/demos/demo_dml_chunking.py
```

#### Generate Embeddings
```bash
python examples/demos/demo_embedding_generator.py
```

#### Test Pattern Recognition
```bash
python examples/demos/demo_pattern_aware_chunker.py
```

### Demo Script Features

Each demo script includes:
- **Setup**: Automatic configuration and initialization
- **Examples**: Multiple usage scenarios
- **Output**: Detailed output showing results
- **Explanations**: Comments explaining each step
- **Error Handling**: Demonstration of error scenarios

## 📋 Demo Categories

### Core Functionality
- **Orchestrator Demo**: End-to-end pipeline processing
- **Chunking Demos**: Various chunking strategies and configurations
- **Embedding Demos**: Different embedding providers and techniques

### Specialized Features
- **DML Processing**: Simics DML file processing examples
- **Pattern Recognition**: Technical documentation pattern detection
- **Metadata Extraction**: Rich metadata generation examples

### Integration Examples
- **Error Handling**: Robust error handling scenarios
- **Configuration**: Different configuration examples
- **Performance**: Performance optimization demonstrations

## 🔧 Customizing Demos

### Configuration
Most demos can be customized by:
1. Modifying configuration parameters at the top of scripts
2. Changing input files and data sources
3. Adjusting processing parameters
4. Enabling/disabling specific features

### Input Data
Demos use sample data from various sources:
- Built-in sample documents
- Test fixtures from `/tests/fixtures/`
- Real documentation examples
- Synthetic test data

### Output Formats
Demo outputs are available in multiple formats:
- JSON for structured data
- Text files for readable output
- Logs for debugging information
- Visualizations (when applicable)

## 📝 Creating New Examples

When adding new examples:
1. Place demo scripts in `/demos/` directory
2. Save output examples in `/outputs/` directory
3. Create notebooks in `/notebooks/` for interactive content
4. Include clear documentation and comments
5. Provide example input data
6. Test with different configurations
7. Update this README with new examples

## 🚀 Advanced Usage

### Batch Processing
```bash
# Process multiple files
python examples/demos/demo_orchestrator.py --batch-mode input_directory/
```

### Configuration Variants
```bash
# Use different embedding providers
python examples/demos/demo_embedding_generator.py --provider qwen
python examples/demos/demo_embedding_generator.py --provider openai
```

### Performance Testing
```bash
# Run with performance monitoring
python examples/demos/demo_orchestrator.py --profile --verbose
```