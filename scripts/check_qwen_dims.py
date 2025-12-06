#!/usr/bin/env python3
"""
Check what dimensions Qwen embeddings actually produce.
"""

import os
import sys

# Add the parent directory to the path to import src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_qwen_dimensions():
    """Check Qwen embedding dimensions."""
    try:
        # Test Qwen embeddings
        print("=== Testing Qwen Embedding Dimensions ===")
        
        # Temporarily enable Qwen
        os.environ['USE_QWEN_EMBEDDINGS'] = 'true'
        os.environ['USE_COPILOT_EMBEDDINGS'] = 'false'
        
        from src.utils import create_embedding, get_qwen_embedding_model
        
        # Check if Qwen model is available
        model = get_qwen_embedding_model()
        if model is None:
            print("Qwen model not available")
            return False
            
        print(f"Qwen model loaded: {type(model)}")
        
        # Test embedding creation
        test_text = "test embedding dimension"
        qwen_embedding = create_embedding(test_text)
        
        print(f"Qwen embedding dimensions: {len(qwen_embedding)}")
        print(f"First 5 values: {qwen_embedding[:5]}")
        
        # Check if this matches what's in the database
        if len(qwen_embedding) == 19309:
            print("✅ Qwen embedding dimensions match database!")
        else:
            print(f"❌ Qwen embedding dimensions ({len(qwen_embedding)}) don't match database (19309)")
            
        return True
        
    except Exception as e:
        print(f"Error checking Qwen dimensions: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_solution():
    """Check what the solution should be."""
    print("\n=== Solution Analysis ===")
    print("The issue is clear:")
    print("1. Database contains embeddings with 19,309 dimensions (likely from Qwen)")
    print("2. Current search is using 1,536 dimension embeddings (GitHub Copilot/OpenAI)")
    print("3. Vector similarity search fails due to dimension mismatch")
    print()
    print("Solutions:")
    print("A. Re-create all embeddings with consistent dimensions (1536)")
    print("B. Use the same embedding model for search as was used for storage")
    print("C. Update database schema to match the actual embedding dimensions")
    print()
    
    # Check current environment
    qwen_enabled = os.getenv('USE_QWEN_EMBEDDINGS', 'false').lower() == 'true'
    copilot_enabled = os.getenv('USE_COPILOT_EMBEDDINGS', 'false').lower() == 'true'
    
    print("Current configuration:")
    print(f"  USE_QWEN_EMBEDDINGS: {os.getenv('USE_QWEN_EMBEDDINGS', 'false')}")
    print(f"  USE_COPILOT_EMBEDDINGS: {os.getenv('USE_COPILOT_EMBEDDINGS', 'false')}")
    print()
    
    if not qwen_enabled:
        print("🔧 Quick fix: Enable Qwen embeddings for search to match database:")
        print("   Set USE_QWEN_EMBEDDINGS=true in your environment")
    else:
        print("⚠️  Qwen is enabled but search is still failing - need to investigate further")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    check_qwen_dimensions()
    check_solution()
