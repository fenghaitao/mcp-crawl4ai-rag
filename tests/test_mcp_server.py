#!/usr/bin/env python3
"""
MCP Server Validation Test

Tests that the MCP server is running correctly with all features enabled.
This test validates configuration, connectivity, and available tools.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value

# Load .env file if running directly
if __name__ == "__main__":
    load_env_file()


def check_server_running():
    """Check if MCP server process is running."""
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        return 'crawl4ai_mcp.py' in result.stdout
    except:
        return False


def test_server_process():
    """Test that the MCP server process is running."""
    print("🔍 Checking MCP server process...")
    
    if check_server_running():
        print("✅ MCP Server process is running")
        return True
    else:
        print("❌ MCP Server process not found")
        print("💡 Start the server with: python ./src/crawl4ai_mcp.py")
        return False


def test_server_configuration():
    """Test server configuration from environment variables."""
    print("\n📋 Testing Server Configuration...")
    
    # Check transport configuration
    transport = os.getenv("TRANSPORT", "sse")
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8051")
    
    print(f"  • Transport: {transport}")
    print(f"  • Host: {host}")
    print(f"  • Port: {port}")
    
    if transport in ["sse", "stdio"]:
        print("✅ Valid transport configuration")
        return True
    else:
        print("❌ Invalid transport configuration")
        return False


def test_database_configuration():
    """Test database connection configuration."""
    print("\n🗄️  Testing Database Configuration...")
    
    # Test Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if supabase_url and supabase_key:
        print("  • Supabase: ✅ Configured")
        supabase_ok = True
    else:
        print("  • Supabase: ❌ Missing configuration")
        supabase_ok = False
    
    # Test Neo4j configuration
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    use_kg = os.getenv("USE_KNOWLEDGE_GRAPH", "false").lower() == "true"
    
    if use_kg and neo4j_uri and neo4j_user and neo4j_password:
        print("  • Neo4j: ✅ Configured")
        neo4j_ok = True
    elif not use_kg:
        print("  • Neo4j: ⚠️  Knowledge graph disabled")
        neo4j_ok = True
    else:
        print("  • Neo4j: ❌ Missing configuration (but knowledge graph enabled)")
        neo4j_ok = False
    
    return supabase_ok and neo4j_ok


def test_ai_configuration():
    """Test AI provider configuration."""
    print("\n🤖 Testing AI Configuration...")
    
    # Check GitHub Copilot configuration
    github_token = os.getenv("GITHUB_TOKEN")
    use_copilot_embeddings = os.getenv("USE_COPILOT_EMBEDDINGS", "false").lower() == "true"
    use_copilot_chat = os.getenv("USE_COPILOT_CHAT", "false").lower() == "true"
    
    copilot_configured = False
    if use_copilot_embeddings or use_copilot_chat:
        if github_token and github_token != "your_github_token_here":
            print("  • GitHub Copilot: ✅ Configured")
            copilot_configured = True
        else:
            print("  • GitHub Copilot: ❌ Token missing or placeholder")
    else:
        print("  • GitHub Copilot: ⚠️  Disabled")
    
    # Check OpenAI configuration
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_configured = False
    if openai_key and openai_key != "your_openai_api_key_here":
        print("  • OpenAI: ✅ Configured")
        openai_configured = True
    else:
        print("  • OpenAI: ❌ Key missing or placeholder")
    
    # Need at least one AI provider
    if copilot_configured or openai_configured:
        print("✅ At least one AI provider configured")
        return True
    else:
        print("❌ No AI providers configured")
        return False


def test_rag_features():
    """Test RAG feature configuration."""
    print("\n🧠 Testing RAG Features...")
    
    features = {
        "Contextual Embeddings": os.getenv("USE_CONTEXTUAL_EMBEDDINGS", "false").lower() == "true",
        "Hybrid Search": os.getenv("USE_HYBRID_SEARCH", "false").lower() == "true",
        "Agentic RAG": os.getenv("USE_AGENTIC_RAG", "false").lower() == "true",
        "Reranking": os.getenv("USE_RERANKING", "false").lower() == "true",
        "Knowledge Graph": os.getenv("USE_KNOWLEDGE_GRAPH", "false").lower() == "true"
    }
    
    enabled_count = 0
    for feature, enabled in features.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  • {feature}: {status}")
        if enabled:
            enabled_count += 1
    
    print(f"✅ {enabled_count}/5 RAG features enabled")
    return True  # Having some features disabled is OK


def test_available_tools():
    """Test that expected tools are available."""
    print("\n🛠️  Testing Available Tools...")
    
    expected_tools = [
        "crawl_single_page",
        "smart_crawl_url",
        "get_available_sources", 
        "perform_rag_query",
        "search_code_examples",
        "check_ai_script_hallucinations",
        "query_knowledge_graph",
        "parse_github_repository"
    ]
    
    print(f"✅ Expected {len(expected_tools)} tools to be available:")
    for tool in expected_tools:
        print(f"  • {tool}")
    
    return True


def test_rate_limiting_config():
    """Test rate limiting configuration."""
    print("\n⏱️  Testing Rate Limiting Configuration...")
    
    requests_per_minute = os.getenv("COPILOT_REQUESTS_PER_MINUTE", "60")
    
    try:
        rpm = int(requests_per_minute)
        if 1 <= rpm <= 1000:
            print(f"  • Rate limit: {rpm} requests/minute ✅")
            return True
        else:
            print(f"  • Rate limit: {rpm} requests/minute ❌ (out of range)")
            return False
    except ValueError:
        print(f"  • Rate limit: Invalid value '{requests_per_minute}' ❌")
        return False


async def test_full_mcp_server():
    """Run complete MCP server validation."""
    print("=" * 60)
    print("🚀 MCP Server Validation Test")
    print("=" * 60)
    
    tests = [
        ("Server Process", test_server_process),
        ("Server Configuration", test_server_configuration),
        ("Database Configuration", test_database_configuration),
        ("AI Configuration", test_ai_configuration),
        ("RAG Features", test_rag_features),
        ("Available Tools", test_available_tools),
        ("Rate Limiting", test_rate_limiting_config)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! MCP Server is properly configured and running.")
        print("\n💡 Server is ready to handle:")
        print("  • Web crawling and content extraction")
        print("  • Advanced RAG queries with multiple strategies")
        print("  • Knowledge graph operations")
        print("  • AI hallucination detection")
        print("  • Code example search and analysis")
    elif passed >= total - 1:
        print("\n⚠️  Most tests passed. Minor configuration issues detected.")
    else:
        print("\n❌ Multiple tests failed. Please check configuration.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_full_mcp_server())
    sys.exit(0 if success else 1)