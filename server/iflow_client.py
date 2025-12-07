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
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Log invocation details
    logger.info(f"🤖 iFlow LLM Invocation")
    logger.info(f"   📋 Model: {model}")
    logger.info(f"   🌡️  Temperature: {temperature}")
    logger.info(f"   🎛️  Max tokens: {max_tokens}")
    logger.info(f"   💬 Message count: {len(messages)}")
    
    # Log message preview (truncated for privacy/readability)
    if messages:
        first_msg = messages[0]
        content = first_msg.get('content', '')
        content_preview = content[:150] + ('...' if len(content) > 150 else '')
        logger.info(f"   📝 First message ({first_msg.get('role', 'unknown')}): {content_preview}")
        
        # Log total content length
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        logger.debug(f"   📏 Total content length: {total_chars} characters")

    # Get API key
    api_key = os.getenv("IFLOW_API_KEY")
    if not api_key:
        logger.error("❌ IFLOW_API_KEY environment variable must be set")
        raise ValueError("IFLOW_API_KEY environment variable must be set")
    api_base = os.getenv("IFLOW_API_BASE", "https://apis.iflow.cn/v1/")
    
    # Convert iflow/ prefix to dashscope/ for LiteLLM
    original_model = model
    if model.startswith("iflow/"):
        model = model.replace("iflow/", "dashscope/")
    elif not model.startswith("dashscope/"):
        model = "dashscope/" + model
    
    if original_model != model:
        logger.debug(f"   🔄 Model conversion: {original_model} -> {model}")
    
    logger.debug(f"   🔗 API Base: {api_base}")
    api_key_preview = f"{'*' * (len(api_key) - 4)}{api_key[-4:]}" if len(api_key) > 4 else "****"
    logger.debug(f"   🔑 API Key: {api_key_preview}")

    # Get rate limiter and wait if needed
    rate_limiter = get_rate_limiter()
    rate_limiter.wait_if_needed()

    start_time = time.time()
    try:
        logger.info("🚀 Making iFlow API request via LiteLLM...")
        
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
        
        elapsed_time = time.time() - start_time
        
        # Record successful request
        rate_limiter.record_success()
        
        # Extract response details for logging
        response_content = response.choices[0].message.content if response.choices else ""
        response_preview = response_content[:150] + ('...' if len(response_content) > 150 else '')
        
        usage = response.usage if response.usage else None
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        
        # Log successful response
        logger.info(f"✅ iFlow API request successful!")
        logger.info(f"   ⏱️  Response time: {elapsed_time:.2f}s")
        logger.info(f"   🏷️  Model used: {response.model}")
        logger.info(f"   🎯 Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        logger.info(f"   📄 Response preview: {response_preview}")
        logger.info(f"   ✋ Finish reason: {response.choices[0].finish_reason if response.choices else 'unknown'}")
        
        # Calculate tokens per second if we have the data
        if completion_tokens > 0:
            tokens_per_sec = completion_tokens / elapsed_time
            logger.debug(f"   📈 Generation speed: {tokens_per_sec:.1f} tokens/second")
        
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
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        # Record error for backoff
        rate_limiter.record_error(e)
        
        logger.error(f"❌ iFlow API request failed after {elapsed_time:.2f}s")
        logger.error(f"   📋 Model: {original_model}")
        logger.error(f"   🚨 Error type: {type(e).__name__}")
        logger.error(f"   💥 Error details: {str(e)[:200]}{'...' if len(str(e)) > 200 else ''}")
        
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
