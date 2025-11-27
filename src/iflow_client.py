"""
iFlow client for Qwen models via LiteLLM.
Provides chat completion functionality using LiteLLM's unified interface.
"""
import os
import time
from typing import List, Dict, Any, Optional
import litellm


class RateLimiter:
    """Rate limiter for API requests with exponential backoff."""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_limit: Maximum burst requests before throttling
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_times = []
        self.consecutive_errors = 0
        self.last_error_time = 0
        
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Check if we need to wait for rate limit
        if len(self.request_times) >= self.requests_per_minute:
            oldest_request = min(self.request_times)
            sleep_time = 60 - (now - oldest_request)
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                return self.wait_if_needed()
        
        # Check burst limit
        recent_requests = [t for t in self.request_times if now - t < 10]  # Last 10 seconds
        if len(recent_requests) >= self.burst_limit:
            sleep_time = 10 - (now - min(recent_requests))
            if sleep_time > 0:
                print(f"Burst limit reached, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
                return self.wait_if_needed()
        
        # Exponential backoff for consecutive errors
        if self.consecutive_errors > 0:
            backoff_time = min(2 ** self.consecutive_errors, 30)  # Max 30 seconds
            if now - self.last_error_time < backoff_time:
                sleep_time = backoff_time - (now - self.last_error_time)
                print(f"Error backoff, waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)
    
    def record_success(self) -> None:
        """Record a successful request."""
        self.consecutive_errors = 0
    
    def record_error(self, error: Exception) -> None:
        """Record an error and determine backoff."""
        self.last_error_time = time.time()
        error_str = str(error).lower()
        
        # Check for rate limit errors
        if "rate" in error_str or "429" in error_str:
            self.consecutive_errors += 1
            print(f"Rate limit error, consecutive errors: {self.consecutive_errors}")
        # Check for server errors
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            self.consecutive_errors += 1
            print(f"Server error, consecutive errors: {self.consecutive_errors}")
        else:
            # Don't increment for other errors
            pass


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        # Get rate limit from environment variable
        requests_per_minute = int(os.getenv("DASHSCOPE_REQUESTS_PER_MINUTE", "60"))
        burst_limit = int(os.getenv("DASHSCOPE_BURST_LIMIT", "10"))
        _rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            burst_limit=burst_limit
        )
    
    return _rate_limiter


def create_chat_completion_iflow(
    messages: List[Dict[str, str]],
    model: str = "iflow/qwen3-coder-plus",
    temperature: float = 0.3,
    max_tokens: int = 500,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a chat completion using iFlow via LiteLLM.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use (default: iflow/qwen3-coder-plus)
        temperature: Temperature for generation (0.0-2.0)
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        Chat completion response in OpenAI-compatible format
        
    Raises:
        Exception: If API call fails
    """
    # Get API key
    api_key = os.getenv("IFLOW_API_KEY")
    if not api_key:
        raise ValueError("IFLOW_API_KEY environment variable must be set")
    api_base = os.getenv("IFLOW_API_BASE", "https://apis.iflow.cn/v1/")
    
    # Convert iflow/ prefix to dashscope/ for LiteLLM
    if model.startswith("iflow/"):
        model = model.replace("iflow/", "dashscope/")
    elif not model.startswith("dashscope/"):
        model = "dashscope/" + model

    # Get rate limiter and wait if needed
    rate_limiter = get_rate_limiter()
    rate_limiter.wait_if_needed()

    try:
        # Use LiteLLM for the API call
        # LiteLLM automatically handles the DashScope API
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            api_base=api_base,
            **kwargs
        )
        
        # Record successful request
        rate_limiter.record_success()
        
        # Convert LiteLLM response to dictionary format
        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content,
                        "role": response.choices[0].message.role
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
            ],
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }
        
    except Exception as e:
        # Record error for backoff
        rate_limiter.record_error(e)
        raise Exception(f"iFlow API request failed via LiteLLM: {e}")


def test_iflow_connection():
    """Test iFlow API connection via LiteLLM."""
    try:
        response = create_chat_completion_iflow(
            messages=[{"role": "user", "content": "Hello, respond with 'OK' if you can read this."}],
            model="iflow/qwen3-coder-plus",
            max_tokens=10
        )
        
        content = response["choices"][0]["message"]["content"]
        print(f"✓ iFlow connection successful via LiteLLM!")
        print(f"  Model: {response.get('model', 'iflow/qwen3-coder-plus')}")
        print(f"  Response: {content}")
        print(f"  Usage: {response.get('usage', {})}")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print(f"  Make sure IFLOW_API_KEY is set in .env")
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test the connection
    test_iflow_connection()
