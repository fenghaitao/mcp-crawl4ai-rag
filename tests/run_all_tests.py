#!/usr/bin/env python3
"""
Test Runner for crawl4ai-mcp

Runs all integration tests for the project.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"Loading environment variables from: {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment (CLI args take precedence)
                    if key not in os.environ:
                        os.environ[key] = value
        print("✅ Environment variables loaded from .env file")
    else:
        print(f"⚠️  No .env file found at: {env_file}")
        print("   Please ensure environment variables are set manually")

# Load .env file before doing anything else
load_env_file()

def run_neo4j_tests():
    """Run Neo4j integration tests."""
    print("\n" + "=" * 60)
    print("Running Neo4j Integration Tests")
    print("=" * 60)
    
    try:
        from tests.test_neo4j_integration import test_full_neo4j_integration
        test_full_neo4j_integration()
        return True
    except Exception as e:
        print(f"❌ Neo4j tests failed: {e}")
        return False

def run_copilot_tests():
    """Run GitHub Copilot integration tests."""
    print("\n" + "=" * 60)
    print("Running GitHub Copilot Integration Tests")
    print("=" * 60)
    
    try:
        from tests.test_copilot_integration import test_full_copilot_integration
        test_full_copilot_integration()
        return True
    except Exception as e:
        print(f"❌ Copilot tests failed: {e}")
        return False

def check_environment():
    """Check environment configuration."""
    print("=" * 60)
    print("Environment Configuration Check")
    print("=" * 60)
    
    # Check required environment variables
    env_vars = {
        "NEO4J_URI": os.getenv("NEO4J_URI"),
        "NEO4J_USER": os.getenv("NEO4J_USER"), 
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
        "USE_KNOWLEDGE_GRAPH": os.getenv("USE_KNOWLEDGE_GRAPH"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "USE_COPILOT_EMBEDDINGS": os.getenv("USE_COPILOT_EMBEDDINGS"),
        "USE_COPILOT_CHAT": os.getenv("USE_COPILOT_CHAT"),
    }
    
    print("Environment Variables:")
    for var, value in env_vars.items():
        if value:
            if "TOKEN" in var or "KEY" in var or "PASSWORD" in var:
                display_value = f"{'*' * min(len(value), 8)}"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    # Check critical configurations
    critical_missing = []
    if not env_vars["NEO4J_URI"] or not env_vars["NEO4J_PASSWORD"]:
        critical_missing.append("Neo4j configuration")
    
    if not env_vars["GITHUB_TOKEN"] and not env_vars["OPENAI_API_KEY"]:
        critical_missing.append("AI API credentials (either GitHub or OpenAI)")
    
    if critical_missing:
        print(f"\n⚠️  Critical configuration missing: {', '.join(critical_missing)}")
        return False
    else:
        print("\n✅ All critical configurations present")
        return True

def main():
    """Main test runner."""
    print("🚀 crawl4ai-mcp Integration Test Suite")
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please configure missing variables.")
        return False
    
    results = []
    
    # Run Neo4j tests
    results.append(("Neo4j Integration", run_neo4j_tests()))
    
    # Run Copilot tests
    results.append(("GitHub Copilot Integration", run_copilot_tests()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)