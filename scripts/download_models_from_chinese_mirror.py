#!/usr/bin/env python
#coding:utf8
"""
Script to download cross-encoder/ms-marco-MiniLM-L-6-v2 reranker model from Chinese HF mirror
"""

import os
import sys
from huggingface_hub import hf_hub_download, HfApi
from pathlib import Path
import shutil


def download_reranker_model():
    """Download cross-encoder/ms-marco-MiniLM-L-6-v2 model files from Chinese mirror"""
    print("Downloading cross-encoder/ms-marco-MiniLM-L-6-v2 from Chinese mirror...")
    
    # Set the mirror environment variable
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    # Also set token to empty to avoid auth issues
    os.environ['HF_TOKEN'] = ''
    
    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    local_dir = "./models/ms-marco-MiniLM-L-6-v2"
    
    try:
        # Create local directory
        os.makedirs(local_dir, exist_ok=True)
        
        # Initialize API with mirror endpoint
        api = HfApi(endpoint='https://hf-mirror.com')
        
        # List files in the repository
        print(f"Listing files in {model_name}...")
        files = api.list_repo_files(repo_id=model_name, repo_type="model")
        
        # Filter for important model files
        model_files = [f for f in files if any(ext in f for ext in ['.json', '.bin', '.safetensors', '.txt', '.py', '.md']) or 'config' in f.lower()]
        
        print(f"Found {len(model_files)} files to download")
        
        # Download each file individually
        for file_name in model_files:
            print(f"Downloading {file_name}...")
            try:
                downloaded_path = hf_hub_download(
                    repo_id=model_name,
                    filename=file_name,
                    cache_dir=local_dir,
                    endpoint='https://hf-mirror.com'
                )
                print(f"Downloaded {file_name} to {downloaded_path}")
            except Exception as e:
                print(f"Warning: Failed to download {file_name}: {e}")
                continue
                
        print("cross-encoder/ms-marco-MiniLM-L-6-v2 downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"Error downloading cross-encoder/ms-marco-MiniLM-L-6-v2: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Starting download of cross-encoder/ms-marco-MiniLM-L-6-v2 reranker model from Chinese HF mirror...")
    
    # Create models directory if it doesn't exist
    os.makedirs("./models", exist_ok=True)
    
    # Download the reranker model
    reranker_success = download_reranker_model()
    
    print("\nDownload process completed!")
    
    if reranker_success:
        print("Reranker model downloaded successfully!")
        print("\n💡 Usage: This is the default reranker model used by crawl4ai-mcp")
        print("   Set USE_RERANKING=true in your .env file to enable reranking")
        return 0
    else:
        print("Download failed. Check error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())