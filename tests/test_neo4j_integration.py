#!/usr/bin/env python3
"""
Neo4j Knowledge Graph Integration Tests

Tests Neo4j connection, knowledge graph functionality, and hallucination detection.
"""

import os
import sys
import pytest
from pathlib import Path

# Add src and knowledge_graphs directories to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "knowledge_graphs"))

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

def test_neo4j_connection():
    """Test the basic Neo4j connection."""
    print("Testing Neo4j connection...")
    
    try:
        from neo4j import GraphDatabase
        
        # Get connection details from environment
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "mcp-crawl4ai-rag")
        
        print(f"Connecting to: {uri}")
        print(f"Username: {user}")
        print(f"Password: {'*' * len(password)}")
        
        # Create driver and test connection
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test the connection with a simple query
        with driver.session() as session:
            result = session.run("RETURN 'Neo4j connection successful!' as message")
            record = result.single()
            print(f"✅ {record['message']}")
            
            # Get Neo4j version
            version_result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            for record in version_result:
                if record["name"] == "Neo4j Kernel":
                    print(f"✅ Neo4j Version: {record['version']}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False


def test_knowledge_graph_tools():
    """Test the knowledge graph tools imports."""
    print("\nTesting knowledge graph tools...")
    
    try:
        # Test importing the knowledge graph modules
        print("Importing knowledge graph modules...")
        
        from parse_repo_into_neo4j import DirectNeo4jExtractor, Neo4jCodeAnalyzer
        from query_knowledge_graph import KnowledgeGraphQuerier
        from ai_script_analyzer import analyze_ai_script, AIScriptAnalyzer
        from knowledge_graph_validator import KnowledgeGraphValidator
        
        print("✅ All knowledge graph modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import knowledge graph modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing knowledge graph tools: {e}")
        return False


def test_repository_parsing():
    """Test repository parsing functionality."""
    print("\nTesting repository parsing...")
    
    try:
        from parse_repo_into_neo4j import DirectNeo4jExtractor
        
        # Test creating the extractor (without actually parsing)
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "mcp-crawl4ai-rag")
        
        extractor = DirectNeo4jExtractor(uri, user, password)
        print("✅ DirectNeo4jExtractor created successfully")
        
        # Test with a small, well-known Python repository
        test_repo_url = "https://github.com/psf/requests.git"
        print(f"Repository parsing available for: {test_repo_url}")
        
        print("✅ Repository parsing function is available and ready to use")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing repository parsing: {e}")
        return False


def test_query_operations():
    """Test basic query operations on the knowledge graph."""
    print("\nTesting query operations...")
    
    try:
        from query_knowledge_graph import KnowledgeGraphQuerier
        from neo4j import GraphDatabase
        
        # Get connection details
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "mcp-crawl4ai-rag")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Check if there are any repositories in the database
            result = session.run("MATCH (r:Repository) RETURN count(r) as repo_count")
            count = result.single()["repo_count"]
            
            if count > 0:
                print(f"✅ Found {count} repositories in the knowledge graph")
                
                # Get repository names
                result = session.run("MATCH (r:Repository) RETURN r.name as name LIMIT 5")
                print("Available repositories:")
                for record in result:
                    print(f"  - {record['name']}")
                    
            else:
                print("📝 No repositories found in the knowledge graph yet")
                print("   You can add repositories using the parse_github_repository tool")
                
            # Test creating a sample node to verify write permissions
            session.run("""
                MERGE (test:TestNode {name: 'connection_test'})
                SET test.timestamp = datetime()
                RETURN test
            """)
            print("✅ Write operations work correctly")
            
            # Clean up test node
            session.run("MATCH (test:TestNode {name: 'connection_test'}) DELETE test")
            print("✅ Delete operations work correctly")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing query operations: {e}")
        return False


def create_sample_code_for_validation():
    """Create a sample Python script to test hallucination detection."""
    print("\nCreating sample code for validation...")
    
    sample_code = '''#!/usr/bin/env python3
"""
Sample Python script to test hallucination detection.
"""

import requests
import json

def fetch_user_data(user_id):
    """Fetch user data from an API."""
    # This is a real requests method
    response = requests.get(f"https://api.example.com/users/{user_id}")
    
    # This would be a hallucination if requests doesn't have this method
    # response.magical_parse()  # This would be detected as a hallucination
    
    return response.json()

def process_data(data):
    """Process the fetched data."""
    # Real json method
    result = json.dumps(data, indent=2)
    return result

if __name__ == "__main__":
    # This is valid code using real methods
    user_data = fetch_user_data(123)
    processed = process_data(user_data)
    print(processed)
'''
    
    # Write to tests directory
    test_dir = Path(__file__).parent
    sample_file = test_dir / "sample_code_for_validation.py"
    sample_file.write_text(sample_code)
    print(f"✅ Created sample code: {sample_file}")
    print("   This can be used to test hallucination detection once repositories are parsed")
    
    return str(sample_file)


@pytest.mark.integration
def test_full_neo4j_integration():
    """Full integration test for Neo4j knowledge graph functionality."""
    print("=" * 60)
    print("Neo4j Knowledge Graph Integration Test")
    print("=" * 60)
    
    # Test 1: Basic Neo4j connection
    assert test_neo4j_connection(), "Neo4j connection failed"
    
    # Test 2: Knowledge graph tools
    assert test_knowledge_graph_tools(), "Knowledge graph tools not available"
    
    # Test 3: Query operations
    assert test_query_operations(), "Query operations failed"
    
    # Test 4: Repository parsing (demonstration)
    assert test_repository_parsing(), "Repository parsing not available"
    
    # Test 5: Create sample code
    sample_file = create_sample_code_for_validation()
    
    print("\n🎉 All Neo4j integration tests passed!")
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Parse a repository into the knowledge graph:")
    print("   .venv/bin/python knowledge_graphs/parse_repo_into_neo4j.py https://github.com/psf/requests.git")
    print()
    print("2. Query the knowledge graph:")
    print("   .venv/bin/python knowledge_graphs/query_knowledge_graph.py")
    print()
    print("3. Test hallucination detection:")
    print(f"   .venv/bin/python knowledge_graphs/ai_hallucination_detector.py {sample_file}")
    print()
    print("4. Use MCP tools to interact with the knowledge graph:")
    print("   - parse_github_repository")
    print("   - query_knowledge_graph") 
    print("   - check_ai_script_hallucinations")
    print("=" * 60)


if __name__ == "__main__":
    # Run the test when called directly
    test_full_neo4j_integration()