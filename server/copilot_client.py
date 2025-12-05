"""
GitHub Copilot Client
Ported from copilot-api/python-port for use in crawl4ai-mcp
Handles both embeddings and chat completions using GitHub Copilot API
"""

import asyncio
import httpx
import os
import json
import uuid
import time
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass
import aiofiles


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
        
    async def wait_if_needed(self) -> None:
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
                await asyncio.sleep(sleep_time)
                return await self.wait_if_needed()
        
        # Check burst limit
        recent_requests = [t for t in self.request_times if now - t < 10]  # Last 10 seconds
        if len(recent_requests) >= self.burst_limit:
            sleep_time = 10 - (now - min(recent_requests))
            if sleep_time > 0:
                print(f"Burst limit reached, waiting {sleep_time:.1f} seconds...")
                await asyncio.sleep(sleep_time)
                return await self.wait_if_needed()
        
        # Exponential backoff for consecutive errors
        if self.consecutive_errors > 0:
            backoff_time = min(2 ** self.consecutive_errors, 30)  # Max 30 seconds
            if now - self.last_error_time < backoff_time:
                sleep_time = backoff_time - (now - self.last_error_time)
                print(f"Error backoff, waiting {sleep_time:.1f} seconds...")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)
    
    def record_success(self) -> None:
        """Record a successful request."""
        self.consecutive_errors = 0
    
    def record_error(self, status_code: int) -> None:
        """Record an error and determine backoff."""
        self.last_error_time = time.time()
        
        if status_code == 429:  # Rate limit exceeded
            self.consecutive_errors += 1
            print(f"Rate limit error, consecutive errors: {self.consecutive_errors}")
        elif status_code >= 500:  # Server errors
            self.consecutive_errors += 1
            print(f"Server error {status_code}, consecutive errors: {self.consecutive_errors}")
        else:
            # Don't increment for client errors (4xx except 429)
            pass


@dataclass
class CopilotEmbeddingResult:
    """Result from Copilot embedding operation."""
    embeddings: List[List[float]]
    model: str
    usage: Dict[str, int]
    texts: List[str]
    
    def __len__(self) -> int:
        """Return number of embeddings."""
        return len(self.embeddings)
    
    def __getitem__(self, index: int) -> List[float]:
        """Get embedding by index."""
        return self.embeddings[index]


class CopilotClient:
    """GitHub Copilot Client for crawl4ai-mcp. Handles both embeddings and chat completions."""
    
    def __init__(self, github_token: Optional[str] = None, requests_per_minute: Optional[int] = None):
        """
        Initialize the Copilot client.
        
        Args:
            github_token: GitHub token. If None, will try to load from environment.
            requests_per_minute: Rate limit for API requests. If None, loads from COPILOT_REQUESTS_PER_MINUTE env var (default: 60)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.copilot_token: Optional[str] = None
        self.vscode_version = "1.85.0"
        
        # Get rate limit from environment if not specified
        if requests_per_minute is None:
            requests_per_minute = int(os.getenv("COPILOT_REQUESTS_PER_MINUTE", "60"))
        
        self.rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)
        
    async def _ensure_authenticated(self) -> None:
        """Ensure we have valid GitHub and Copilot tokens."""
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        if not self.copilot_token:
            self.copilot_token = await self._get_copilot_token()
    
    async def _get_copilot_token(self) -> str:
        """Get Copilot API token."""
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "authorization": f"token {self.github_token}",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": "copilot-chat/0.26.7",
            "user-agent": "GitHubCopilotChat/0.26.7",
            "x-github-api-version": "2025-04-01",
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/copilot_internal/v2/token",
                headers=headers,
            )
            
            if not response.is_success:
                raise Exception(f"Failed to get Copilot token: {response.status_code} {response.text}")
            
            data = response.json()
            return data["token"]
    
    def _get_copilot_base_url(self, account_type: str = "individual") -> str:
        """Get Copilot API base URL."""
        if account_type == "individual":
            return "https://api.githubcopilot.com"
        return f"https://api.{account_type}.githubcopilot.com"
    
    def _get_copilot_headers(self) -> Dict[str, str]:
        """Get headers for Copilot API requests."""
        return {
            "Authorization": f"Bearer {self.copilot_token}",
            "content-type": "application/json",
            "copilot-integration-id": "vscode-chat",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": "copilot-chat/0.26.7",
            "user-agent": "GitHubCopilotChat/0.26.7",
            "openai-intent": "conversation-panel",
            "x-github-api-version": "2025-04-01",
            "x-request-id": str(uuid.uuid4()),
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
    
    async def create_embeddings(
        self, 
        texts: Union[str, List[str]], 
        model: str = "text-embedding-3-small",
        account_type: str = "individual"
    ) -> CopilotEmbeddingResult:
        """
        Create embeddings for the given texts.
        
        Args:
            texts: Single text string or list of text strings to embed
            model: Embedding model to use (default: text-embedding-3-small)
            account_type: GitHub account type (individual, business, enterprise)
            
        Returns:
            CopilotEmbeddingResult with embeddings, model info, and usage data
        """
        await self._ensure_authenticated()
        
        # Ensure texts is a list
        if isinstance(texts, str):
            text_list = [texts]
        else:
            text_list = texts
        
        payload = {
            "input": text_list,
            "model": model
        }
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._get_copilot_base_url(account_type)}/embeddings",
                headers=self._get_copilot_headers(),
                json=payload,
                timeout=30.0
            )
            
            if not response.is_success:
                self.rate_limiter.record_error(response.status_code)
                
                # If token is expired, clear it and retry once
                if response.status_code == 401:
                    print("Copilot token expired, refreshing...")
                    self.copilot_token = None
                    await self._ensure_authenticated()
                    
                    # Rate limit the retry as well
                    await self.rate_limiter.wait_if_needed()
                    
                    response = await client.post(
                        f"{self._get_copilot_base_url(account_type)}/embeddings",
                        headers=self._get_copilot_headers(),
                        json=payload,
                        timeout=30.0
                    )
                
                if not response.is_success:
                    self.rate_limiter.record_error(response.status_code)
                    raise Exception(f"Failed to create embeddings: {response.status_code} {response.text}")
            
            # Record successful request
            self.rate_limiter.record_success()
            
            data = response.json()
            
            # Extract embeddings
            embeddings = [item["embedding"] for item in data["data"]]
            
            return CopilotEmbeddingResult(
                embeddings=embeddings,
                model=data.get("model", model),
                usage=data.get("usage", {}),
                texts=text_list
            )
    
    async def create_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Create embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Size of each batch
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                result = await self.create_embeddings(batch)
                all_embeddings.extend(result.embeddings)
                
                # Small delay between batches (rate limiter handles the main throttling)
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                raise RuntimeError(f"Error creating embeddings for batch {i//batch_size + 1}: {e}")
                # Add zero embeddings as fallback
                for _ in batch:
                    all_embeddings.append([0.0] * 1536)  # text-embedding-3-small dimension
        
        return all_embeddings
    
    async def create_embedding_single(self, text: str) -> List[float]:
        """
        Create a single embedding.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding as list of floats
        """
        try:
            result = await self.create_embeddings(text)
            return result.embeddings[0]
        except Exception as e:
            print(f"Error creating single embedding: {e}")
            return [0.0] * 1536  # Fallback zero embedding

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 200,
        account_type: str = "individual",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using GitHub Copilot API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use for chat completion (default: gpt-4o)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            account_type: GitHub account type
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        await self._ensure_authenticated()
        
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._get_copilot_base_url(account_type)}/chat/completions",
                headers=self._get_copilot_headers(),
                json=payload,
                timeout=60.0
            )
            
            if not response.is_success:
                self.rate_limiter.record_error(response.status_code)
                
                # If token is expired, clear it and retry once
                if response.status_code == 401:
                    print("Copilot token expired, refreshing...")
                    self.copilot_token = None
                    await self._ensure_authenticated()
                    
                    # Rate limit the retry as well
                    await self.rate_limiter.wait_if_needed()
                    
                    response = await client.post(
                        f"{self._get_copilot_base_url(account_type)}/chat/completions",
                        headers=self._get_copilot_headers(),
                        json=payload,
                        timeout=60.0
                    )
                
                if not response.is_success:
                    self.rate_limiter.record_error(response.status_code)
                    raise Exception(f"Failed to create chat completion: {response.status_code} {response.text}")
            
            # Record successful request
            self.rate_limiter.record_success()
            
            return response.json()

    async def initialize(self) -> bool:
        """
        Initialize the client by getting Copilot token.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.github_token:
                print("No GitHub token provided. Please set GITHUB_TOKEN environment variable.")
                return False
            
            # Get Copilot token
            await self._ensure_authenticated()
            print("Successfully obtained Copilot token")
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize Copilot client: {e}")
            return False


# Global client instance
_copilot_client: Optional[CopilotClient] = None


async def get_copilot_client() -> Optional[CopilotClient]:
    """
    Get or create the global Copilot client instance.
    
    Returns:
        Initialized CopilotClient or None if initialization fails
    """
    global _copilot_client
    
    if _copilot_client is None:
        _copilot_client = CopilotClient()
        if not await _copilot_client.initialize():
            _copilot_client = None
    
    return _copilot_client


# Sync wrapper functions for backward compatibility
def create_embeddings_batch_copilot(texts: List[str]) -> List[List[float]]:
    """
    Synchronous wrapper for creating embeddings using Copilot.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings
    """
    async def _create():
        try:
            client = await get_copilot_client()
            if client is None:
                print("Copilot client not available, falling back to zero embeddings")
                return [[0.0] * 1536 for _ in texts]
            
            return await client.create_embeddings_batch(texts)
        except Exception as e:
            print(f"Error in Copilot batch embeddings: {e}")
            return [[0.0] * 1536 for _ in texts]
    
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an event loop, so we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _create())
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(_create())
    except Exception as e:
        print(f"Error running async Copilot batch embeddings: {e}")
        return [[0.0] * 1536 for _ in texts]


def create_embedding_copilot(text: str) -> List[float]:
    """
    Synchronous wrapper for creating a single embedding using Copilot.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding as list of floats
    """
    async def _create():
        try:
            client = await get_copilot_client()
            if client is None:
                print("Copilot client not available, falling back to zero embedding")
                return [0.0] * 1536
            
            return await client.create_embedding_single(text)
        except Exception as e:
            print(f"Error in Copilot single embedding: {e}")
            return [0.0] * 1536
    
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an event loop, so we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _create())
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(_create())
    except Exception as e:
        print(f"Error running async Copilot single embedding: {e}")
        return [0.0] * 1536


def create_chat_completion_copilot(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 200,
    **kwargs
) -> Dict[str, Any]:
    """
    Synchronous wrapper for creating chat completions using Copilot.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Model to use for chat completion
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        Chat completion response
    """
    async def _create():
        try:
            client = await get_copilot_client()
            if client is None:
                raise Exception("Copilot client not available")
            
            return await client.create_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except Exception as e:
            print(f"Error in Copilot chat completion: {e}")
            raise
    
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            # If we get here, we're in an event loop, so we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _create())
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(_create())
    except Exception as e:
        print(f"Error running async Copilot chat completion: {e}")
        raise