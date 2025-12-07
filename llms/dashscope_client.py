"""
DashScope client for Alibaba Cloud's Qwen models.
Provides chat completion functionality using DashScope API.
"""
import os
import requests
from typing import List, Dict, Any, Optional


def create_chat_completion_dashscope(
    messages: List[Dict[str, str]],
    model: str = "qwen-coder-plus",
    temperature: float = 0.3,
    max_tokens: int = 500,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a chat completion using DashScope API (Alibaba Cloud).
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use (default: qwen-coder-plus)
        temperature: Temperature for generation (0.0-2.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        Chat completion response in OpenAI-compatible format
        
    Raises:
        Exception: If API call fails
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY environment variable not set")
    
    # DashScope API endpoint
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    # Prepare request headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare request body
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs
    }
    
    try:
        # Make API request
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        # Return in OpenAI-compatible format
        return {
            "choices": [
                {
                    "message": {
                        "content": result["choices"][0]["message"]["content"],
                        "role": result["choices"][0]["message"]["role"]
                    },
                    "finish_reason": result["choices"][0].get("finish_reason", "stop")
                }
            ],
            "model": result.get("model", model),
            "usage": result.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"DashScope API request failed: {e}")
    except (KeyError, IndexError) as e:
        raise Exception(f"Failed to parse DashScope API response: {e}")


def test_dashscope_connection():
    """Test DashScope API connection."""
    try:
        response = create_chat_completion_dashscope(
            messages=[{"role": "user", "content": "Hello, respond with 'OK' if you can read this."}],
            model="qwen-coder-plus",
            max_tokens=10
        )
        
        content = response["choices"][0]["message"]["content"]
        print(f"✓ DashScope connection successful!")
        print(f"  Model: {response['model']}")
        print(f"  Response: {content}")
        return True
        
    except Exception as e:
        print(f"✗ DashScope connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    test_dashscope_connection()
