# Development Tools & Utilities

This directory contains development tools, utilities, and installation scripts.

## 📁 Directory Structure

### `/install/` - Installation Scripts
Scripts for setting up the development environment:
- Dependency installation
- Environment setup
- Model downloads
- System configuration

### Root Level Tools
Utility scripts for development and maintenance:
- `install_deps_without_sudo.py` - Install dependencies without sudo access
- `convert_html_to_markdown.py` - HTML to Markdown conversion utility
- `verify_summarization_integration.py` - Verification script for summarization features

## 🔧 Installation & Setup Tools

### Dependency Installation
```bash
# Install dependencies without sudo
python tools/install_deps_without_sudo.py

# Alternative: use the scripts in main scripts/ directory
python scripts/download_hf_model.py --models qwen-embedding
```

### Content Processing Tools
```bash
# Convert HTML files to Markdown
python tools/convert_html_to_markdown.py input.html output.md

# Verify summarization integration
python tools/verify_summarization_integration.py
```

## 🛠️ Development Utilities

### File Processing
- HTML to Markdown conversion
- Content format standardization
- Batch file processing

### Verification & Testing
- Integration verification scripts
- System health checks
- Configuration validation

### Environment Setup
- Dependency management
- Model installation
- Configuration setup

## 📝 Adding New Tools

When adding new development tools:
1. Place installation scripts in `/install/`
2. Place general utilities in root of `/tools/`
3. Include clear usage documentation
4. Add error handling and logging
5. Test across different environments
6. Update this README with new tools