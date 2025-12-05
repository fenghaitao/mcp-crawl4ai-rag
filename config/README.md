# Configuration Files

This directory contains configuration files and sample configurations.

## 📁 Directory Structure

### `/samples/` - Sample Configuration Files
Example configurations and reference data:
- `simics_dml_urls.json` - Sample URL configurations for Simics DML documentation
- Example environment configurations
- Sample API configurations
- Reference data files

## ⚙️ Configuration Management

### Environment Variables
Primary configuration through `.env` file in project root:
- Database connection settings
- API keys and authentication
- Feature flags and toggles
- Model and provider configurations

### JSON Configuration Files
Structured configuration data:
- URL lists for web crawling
- Model configurations
- Processing pipelines
- Integration settings

## 🔧 Setup Instructions

1. Copy `.env.example` to `.env` in project root
2. Configure required environment variables
3. Customize JSON configurations as needed
4. Review sample configurations for reference

## 📝 Adding New Configurations

When adding new configuration files:
1. Place sample/reference files in `/samples/`
2. Document configuration options
3. Provide example values
4. Update environment variable documentation
5. Test with different configuration combinations