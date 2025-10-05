#!/usr/bin/env python3
"""
GitHub Copilot Integration Tests

Tests GitHub Copilot embedding and chat completion functionality.
"""

import os
import asyncio
import sys
import pytest
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

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


@pytest.mark.asyncio
async def test_copilot_embeddings():
    """Test the Copilot embedding client."""
    print("Testing GitHub Copilot Embedding Client...")
    
    # Check if GitHub token is available
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    
    print(f"✅ GitHub token found (length: {len(github_token)})")
    
    # Import and initialize client
    from copilot_client import CopilotClient
    client = CopilotClient(github_token)
    
    print("Initializing Copilot client...")
    if not await client.initialize():
        pytest.fail("Failed to initialize Copilot client")
    
    print("✅ Copilot client initialized successfully")
    
    # Test single embedding
    print("\nTesting single embedding...")
    test_text = "This is a test sentence for embedding generation."
    
    try:
        embedding = await client.create_embedding_single(test_text)
        print(f"✅ Single embedding created: dimension {len(embedding)}")
        assert len(embedding) == 1536, f"Expected 1536 dimensions, got {len(embedding)}"
    except Exception as e:
        pytest.fail(f"Error creating single embedding: {e}")
    
    # Test batch embeddings
    print("\nTesting batch embeddings...")
    test_texts = [
        "First test sentence for batch embedding.",
        "Second test sentence for batch embedding.",
        "Third test sentence for batch embedding."
    ]
    
    try:
        embeddings = await client.create_embeddings_batch(test_texts)
        print(f"✅ Batch embeddings created: {len(embeddings)} embeddings, dimension {len(embeddings[0])}")
        assert len(embeddings) == len(test_texts), f"Expected {len(test_texts)} embeddings, got {len(embeddings)}"
        assert len(embeddings[0]) == 1536, f"Expected 1536 dimensions, got {len(embeddings[0])}"
    except Exception as e:
        pytest.fail(f"Error creating batch embeddings: {e}")
    
    # Test chat completion
    print("\nTesting chat completion...")
    try:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a brief summary of what Python is in one sentence."}
        ]
        
        chat_response = await client.create_chat_completion(
            messages=messages,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=50
        )
        
        content = chat_response["choices"][0]["message"]["content"]
        print(f"✅ Chat completion created: {content[:100]}...")
        assert "choices" in chat_response, "Response should contain 'choices'"
        assert len(chat_response["choices"]) > 0, "Response should have at least one choice"
    except Exception as e:
        pytest.fail(f"Error creating chat completion: {e}")

    print("\n🎉 All Copilot tests passed!")


def test_utils_integration():
    """Test the utils.py integration with Copilot embeddings and chat."""
    print("\nTesting utils.py integration...")
    
    # Set environment variables to use Copilot
    original_embeddings = os.environ.get("USE_COPILOT_EMBEDDINGS", "false")
    original_chat = os.environ.get("USE_COPILOT_CHAT", "false")
    
    os.environ["USE_COPILOT_EMBEDDINGS"] = "true"
    os.environ["USE_COPILOT_CHAT"] = "true"
    
    try:
        # Check if GitHub token is available
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            pytest.skip("GITHUB_TOKEN environment variable not set")
        
        from utils import create_embedding, create_embeddings_batch, create_chat_completion
        
        # Test single embedding
        print("Testing single embedding via utils...")
        embedding = create_embedding("Test text for utils integration")
        print(f"✅ Utils single embedding: dimension {len(embedding)}")
        assert len(embedding) == 1536, f"Expected 1536 dimensions, got {len(embedding)}"
        
        # Test batch embeddings
        print("Testing batch embeddings via utils...")
        embeddings = create_embeddings_batch([
            "First utils test",
            "Second utils test"
        ])
        print(f"✅ Utils batch embeddings: {len(embeddings)} embeddings, dimension {len(embeddings[0])}")
        assert len(embeddings) == 2, f"Expected 2 embeddings, got {len(embeddings)}"
        assert len(embeddings[0]) == 1536, f"Expected 1536 dimensions, got {len(embeddings[0])}"
        
        # Test chat completion
        print("Testing chat completion via utils...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is machine learning in one sentence?"}
        ]
        chat_response = create_chat_completion(
            messages=messages,
            model="gpt-4o",
            temperature=0.3,
            max_tokens=50
        )
        content = chat_response["choices"][0]["message"]["content"]
        print(f"✅ Utils chat completion: {content[:100]}...")
        assert "choices" in chat_response, "Response should contain 'choices'"
        
        print("✅ All utils integration tests passed!")
        
    except Exception as e:
        pytest.fail(f"Error testing utils integration: {e}")
    finally:
        # Reset environment variables
        os.environ["USE_COPILOT_EMBEDDINGS"] = original_embeddings
        os.environ["USE_COPILOT_CHAT"] = original_chat


def test_fallback_behavior():
    """Test fallback behavior when Copilot is unavailable."""
    print("\nTesting fallback behavior...")
    
    # Temporarily remove GitHub token to test fallback
    original_token = os.environ.get("GITHUB_TOKEN")
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    
    # Set to use Copilot but without token
    original_embeddings = os.environ.get("USE_COPILOT_EMBEDDINGS", "false")
    original_chat = os.environ.get("USE_COPILOT_CHAT", "false")
    
    os.environ["USE_COPILOT_EMBEDDINGS"] = "true"
    os.environ["USE_COPILOT_CHAT"] = "true"
    
    try:
        # Check if OpenAI is available for fallback
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            pytest.skip("Neither GITHUB_TOKEN nor OPENAI_API_KEY available for fallback test")
        
        from utils import create_embedding, create_chat_completion
        
        # Test embedding fallback
        print("Testing embedding fallback to OpenAI...")
        embedding = create_embedding("Test fallback embedding")
        print(f"✅ Fallback embedding: dimension {len(embedding)}")
        assert len(embedding) == 1536, f"Expected 1536 dimensions, got {len(embedding)}"
        
        # Test chat completion fallback
        print("Testing chat completion fallback to OpenAI...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"}
        ]
        chat_response = create_chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=50
        )
        content = chat_response["choices"][0]["message"]["content"]
        print(f"✅ Fallback chat completion: {content[:100]}...")
        assert "choices" in chat_response, "Response should contain 'choices'"
        
        print("✅ Fallback behavior works correctly!")
        
    except Exception as e:
        pytest.fail(f"Error testing fallback behavior: {e}")
    finally:
        # Restore environment variables
        if original_token:
            os.environ["GITHUB_TOKEN"] = original_token
        os.environ["USE_COPILOT_EMBEDDINGS"] = original_embeddings
        os.environ["USE_COPILOT_CHAT"] = original_chat


@pytest.mark.integration
def test_full_copilot_integration():
    """Full integration test for GitHub Copilot functionality."""
    print("=" * 60)
    print("GitHub Copilot Integration Test")
    print("=" * 60)
    
    # Test 1: Copilot client directly
    asyncio.run(test_copilot_embeddings())
    
    # Test 2: Utils integration
    test_utils_integration()
    
    # Test 3: Fallback behavior
    test_fallback_behavior()
    
    print("\n🎉 All Copilot integration tests passed!")
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY:")
    print("=" * 60)
    print("✅ GitHub Copilot embeddings working")
    print("✅ GitHub Copilot chat completions working")
    print("✅ Utils.py integration working")
    print("✅ Fallback behavior working")
    print()
    print("RECOMMENDED CONFIGURATION:")
    print("USE_COPILOT_EMBEDDINGS=true")
    print("USE_COPILOT_CHAT=true")
    print("GITHUB_TOKEN=your_github_token")
    print("=" * 60)


if __name__ == "__main__":
    # Run the test when called directly
    test_full_copilot_integration()