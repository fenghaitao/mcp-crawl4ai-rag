#!/usr/bin/env python3
"""
Script to download embedding and reranking models used by crawl4ai-mcp

This script can download multiple models:
- cross-encoder/ms-marco-MiniLM-L-6-v2 (default reranker)
- Qwen/Qwen3-Embedding-0.6B (embedding model)
- Qwen/Qwen3-Reranker-0.6B (alternative reranker)

Usage:
    python scripts/download_reranker_model.py [OPTIONS]

Options:
    --models MODEL_NAME     Specify models to download (can be used multiple times)
                           Available: ms-marco, qwen-embedding, qwen-reranker, all
    --test                 Run tests after downloading to verify models work
    --hf-endpoint URL      Use a custom Hugging Face endpoint (e.g., https://hf-mirror.com)
    --list                 List available models
"""
import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path to import from src/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sentence_transformers import CrossEncoder, SentenceTransformer
except ImportError:
    print("❌ Error: sentence-transformers is not installed.")
    print("Please install it with: pip install sentence-transformers")
    sys.exit(1)

# Available models configuration
AVAILABLE_MODELS = {
    "ms-marco": {
        "name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "type": "cross-encoder",
        "description": "Lightweight cross-encoder for reranking (22M params, ~90MB)",
        "use_case": "Default reranker for crawl4ai-mcp"
    },
    "qwen-embedding": {
        "name": "Qwen/Qwen3-Embedding-0.6B",
        "type": "sentence-transformer", 
        "description": "Qwen3 embedding model (0.6B params, ~1.2GB)",
        "use_case": "High-quality embeddings for semantic search"
    },
    "qwen-reranker": {
        "name": "Qwen/Qwen3-Reranker-0.6B",
        "type": "cross-encoder",
        "description": "Qwen3 reranker model (0.6B params, ~1.2GB)", 
        "use_case": "High-performance reranking alternative"
    }
}


def list_models():
    """List all available models."""
    print("📋 Available Models:")
    print("=" * 60)
    for key, info in AVAILABLE_MODELS.items():
        print(f"\n🔑 {key}")
        print(f"   Name: {info['name']}")
        print(f"   Type: {info['type']}")
        print(f"   Size: {info['description']}")
        print(f"   Use:  {info['use_case']}")


def download_models(model_keys, hf_endpoint=None, run_test=False):
    """
    Download specified models.
    
    Args:
        model_keys (list): List of model keys to download
        hf_endpoint (str, optional): Custom Hugging Face endpoint
        run_test (bool): Whether to run tests after downloading
    """
    # Set custom HF endpoint if provided
    if hf_endpoint:
        os.environ['HF_ENDPOINT'] = hf_endpoint
        print(f"Setting Hugging Face endpoint to: {hf_endpoint}")
    
    # Handle 'all' keyword
    if 'all' in model_keys:
        model_keys = list(AVAILABLE_MODELS.keys())
    
    downloaded_models = {}
    
    for model_key in model_keys:
        if model_key not in AVAILABLE_MODELS:
            print(f"❌ Unknown model: {model_key}")
            print(f"Available models: {', '.join(AVAILABLE_MODELS.keys())}")
            continue
            
        model_info = AVAILABLE_MODELS[model_key]
        model_name = model_info['name']
        model_type = model_info['type']
        
        print(f"\n🚀 Downloading {model_key}: {model_name}")
        print(f"   Type: {model_type}")
        print(f"   Description: {model_info['description']}")
        
        try:
            # Download based on model type
            if model_type == "cross-encoder":
                model = CrossEncoder(model_name)
            elif model_type == "sentence-transformer":
                model = SentenceTransformer(model_name)
            else:
                print(f"❌ Unknown model type: {model_type}")
                continue
                
            print(f"✅ {model_key} downloaded successfully!")
            downloaded_models[model_key] = model
            
            # Show cache location
            safe_name = model_name.replace("/", "--")
            cache_dir = os.path.expanduser(f"~/.cache/huggingface/hub/models--{safe_name}")
            if os.path.exists(cache_dir):
                print(f"📂 Cached at: {cache_dir}")
            
        except Exception as e:
            print(f"❌ Error downloading {model_key}: {e}")
            continue
    
    if run_test and downloaded_models:
        print(f"\n🧪 Running tests on {len(downloaded_models)} downloaded models...")
        test_models(downloaded_models)
    
    # Show usage instructions
    print(f"\n✅ Download complete!")
    if 'ms-marco' in downloaded_models or 'qwen-reranker' in downloaded_models:
        print("💡 To enable reranking: Set USE_RERANKING=true in your .env file")
    if 'qwen-embedding' in downloaded_models:
        print("💡 Qwen embedding model can be used for custom embedding tasks")


def test_models(models_dict):
    """
    Test multiple models with sample queries.
    
    Args:
        models_dict: Dictionary of {model_key: model_object}
    """
    # Test case 1: General knowledge
    query1 = "What is machine learning?"
    docs1 = [
        "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
        "The weather forecast shows rain tomorrow.",
        "Deep learning uses neural networks with multiple layers.",
        "Python is a programming language commonly used in data science."
    ]
    
    # Test case 2: Technical query
    query2 = "How to optimize database performance?"
    docs2 = [
        "Database indexing can significantly improve query performance.",
        "Cats are popular pets that require regular veterinary care.",
        "SQL query optimization involves analyzing execution plans.",
        "Database normalization reduces data redundancy."
    ]
    
    test_cases = [
        (query1, docs1, "General Knowledge"),
        (query2, docs2, "Technical Query")
    ]
    
    for model_key, model in models_dict.items():
        model_info = AVAILABLE_MODELS[model_key]
        print(f"\n🔬 Testing {model_key} ({model_info['type']}):")
        print("=" * 50)
        
        if model_info['type'] == 'cross-encoder':
            # Test cross-encoder (reranker)
            test_cross_encoder(model, test_cases, model_key)
        elif model_info['type'] == 'sentence-transformer':
            # Test sentence transformer (embedding)
            test_sentence_transformer(model, test_cases, model_key)


def test_cross_encoder(model, test_cases, model_name):
    """Test a cross-encoder model for reranking."""
    for query, docs, test_name in test_cases:
        print(f"\n📝 {test_name} - Reranking Test:")
        print(f"Query: {query}")
        
        # Create query-document pairs for scoring
        pairs = [[query, doc] for doc in docs]
        scores = model.predict(pairs)
        
        # Sort by score (descending)
        scored_docs = list(zip(docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (doc, score) in enumerate(scored_docs):
            relevance = "🎯" if i == 0 else "📄"
            print(f"  {relevance} {score:7.4f} - {doc[:80]}{'...' if len(doc) > 80 else ''}")


def test_sentence_transformer(model, test_cases, model_name):
    """Test a sentence transformer model for embeddings."""
    for query, docs, test_name in test_cases:
        print(f"\n📝 {test_name} - Embedding Test:")
        print(f"Query: {query}")
        
        # Get embeddings for query and documents
        query_embedding = model.encode([query])
        doc_embeddings = model.encode(docs)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
        
        # Sort by similarity (descending)
        scored_docs = list(zip(docs, similarities))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        for i, (doc, score) in enumerate(scored_docs):
            relevance = "🎯" if i == 0 else "📄"
            print(f"  {relevance} {score:7.4f} - {doc[:80]}{'...' if len(doc) > 80 else ''}")


def test_single_model(model_key, model):
    """Test a single model (for backward compatibility)."""
    test_models({model_key: model})


def main():
    parser = argparse.ArgumentParser(
        description="Download embedding and reranking models for crawl4ai-mcp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List available models
    python scripts/download_reranker_model.py --list
    
    # Download default model (ms-marco)
    python scripts/download_reranker_model.py --models ms-marco
    
    # Download Qwen models
    python scripts/download_reranker_model.py --models qwen-embedding --models qwen-reranker
    
    # Download all models with testing
    python scripts/download_reranker_model.py --models all --test
    
    # Use HF mirror endpoint
    python scripts/download_reranker_model.py --models qwen-embedding --hf-endpoint https://hf-mirror.com --test
        """
    )
    
    parser.add_argument(
        "--models", 
        action="append",
        choices=list(AVAILABLE_MODELS.keys()) + ["all"],
        help="Models to download (can be used multiple times). Use 'all' for all models."
    )
    
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run tests after downloading to verify models work"
    )
    
    parser.add_argument(
        "--hf-endpoint", 
        type=str, 
        help="Custom Hugging Face endpoint (e.g., https://hf-mirror.com)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models and exit"
    )
    
    args = parser.parse_args()
    
    print("🚀 Crawl4AI MCP Model Download Script")
    print("=" * 45)
    
    if args.list:
        list_models()
        return
    
    # Default to ms-marco if no models specified
    models_to_download = args.models or ["ms-marco"]
    
    print(f"\n📦 Models to download: {', '.join(models_to_download)}")
    download_models(models_to_download, hf_endpoint=args.hf_endpoint, run_test=args.test)


if __name__ == "__main__":
    main()
