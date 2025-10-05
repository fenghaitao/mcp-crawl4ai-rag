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
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass
import aiofiles


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
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the Copilot client.
        
        Args:
            github_token: GitHub token. If None, will try to load from environment.
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.copilot_token: Optional[str] = None
        self.vscode_version = "1.85.0"
        self.account_type = "individual"  # Default to individual
        
        # API Configuration
        self.copilot_version = "0.26.7"
        self.editor_plugin_version = f"copilot-chat/{self.copilot_version}"
        self.user_agent = f"GitHubCopilotChat/{self.copilot_version}"
        self.api_version = "2025-04-01"
        
        # GitHub API constants
        self.github_api_base_url = "https://api.github.com"
        self.github_client_id = "Iv1.b507a08c87ecfe98"
        self.github_api_version = "2022-11-28"  # GitHub API uses different version
        
    def _get_copilot_base_url(self) -> str:
        """Get Copilot API base URL based on account type."""
        if self.account_type == "individual":
            return "https://api.githubcopilot.com"
        return f"https://api.{self.account_type}.githubcopilot.com"
    
    def _get_copilot_headers(self) -> Dict[str, str]:
        """Generate headers for Copilot API requests."""
        return {
            "Authorization": f"Bearer {self.copilot_token}",
            "content-type": "application/json",
            "copilot-integration-id": "vscode-chat",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": self.editor_plugin_version,
            "user-agent": self.user_agent,
            "openai-intent": "conversation-panel",
            "x-github-api-version": self.api_version,
            "x-request-id": str(uuid.uuid4()),
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
    
    def _get_github_headers(self) -> Dict[str, str]:
        """Generate headers for GitHub API requests."""
        return {
            "content-type": "application/json",
            "accept": "application/json",
            "authorization": f"token {self.github_token}",
            "editor-version": f"vscode/{self.vscode_version}",
            "editor-plugin-version": self.editor_plugin_version,
            "user-agent": self.user_agent,
            "x-github-api-version": self.github_api_version,  # Use GitHub API version
            "x-vscode-user-agent-library-version": "electron-fetch",
        }
    
    async def _get_copilot_token_from_github(self) -> str:
        """Get Copilot token from GitHub API."""
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base_url}/copilot_internal/v2/token",
                headers=self._get_github_headers()
            )
            
            if not response.is_success:
                raise Exception(f"Failed to get Copilot token: {response.status_code} {response.text}")
            
            data = response.json()
            return data["token"]
    
    async def _get_user_info(self) -> Dict[str, Any]:
        """Get user information from GitHub API."""
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base_url}/user",
                headers=self._get_github_headers()
            )
            
            if not response.is_success:
                raise Exception(f"Failed to get user info: {response.status_code} {response.text}")
            
            return response.json()
    
    async def initialize(self) -> bool:
        """
        Initialize the client by getting Copilot token and user info.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if not self.github_token:
                print("No GitHub token provided. Please set GITHUB_TOKEN environment variable.")
                return False
            
            # Get user info to determine account type
            user_info = await self._get_user_info()
            print(f"Authenticated as: {user_info.get('login', 'Unknown')}")
            
            # Get Copilot token
            self.copilot_token = await self._get_copilot_token_from_github()
            print("Successfully obtained Copilot token")
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize Copilot client: {e}")
            return False
    
    async def create_embeddings(
        self, 
        texts: Union[str, List[str]], 
        model: str = "text-embedding-3-small"
    ) -> CopilotEmbeddingResult:
        """
        Create embeddings using GitHub Copilot API.
        
        Args:
            texts: Text or list of texts to embed
            model: Model to use for embeddings
            
        Returns:
            CopilotEmbeddingResult containing embeddings and metadata
        """
        if not self.copilot_token:
            raise ValueError("Client not initialized. Call initialize() first.")
        
        # Ensure texts is a list
        if isinstance(texts, str):
            input_texts = [texts]
        else:
            input_texts = texts
        
        payload = {
            "input": input_texts,
            "model": model
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._get_copilot_base_url()}/embeddings",
                headers=self._get_copilot_headers(),
                json=payload,
                timeout=30.0
            )
            
            if not response.is_success:
                raise Exception(f"Failed to create embeddings: {response.status_code} {response.text}")
            
            data = response.json()
            
            # Extract embeddings from response
            embeddings = [item["embedding"] for item in data["data"]]
            
            return CopilotEmbeddingResult(
                embeddings=embeddings,
                model=data.get("model", "text-embedding-3-small"),  # Fallback if model not in response
                usage=data.get("usage", {}),  # Fallback if usage not in response
                texts=input_texts
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
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                print(f"Error creating embeddings for batch {i//batch_size + 1}: {e}")
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
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using GitHub Copilot API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use for chat completion (default: gpt-4o)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        if not self.copilot_token:
            raise ValueError("Client not initialized. Call initialize() first.")
        
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._get_copilot_base_url()}/chat/completions",
                headers=self._get_copilot_headers(),
                json=payload,
                timeout=60.0
            )
            
            if not response.is_success:
                raise Exception(f"Failed to create chat completion: {response.status_code} {response.text}")
            
            return response.json()


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
            # If we get here, we're in an event loop, so we can't use asyncio.run()
            print("Already in event loop, cannot use Copilot embeddings in this context")
            return [[0.0] * 1536 for _ in texts]
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
            # If we get here, we're in an event loop, so we can't use asyncio.run()
            print("Already in event loop, cannot use Copilot single embedding in this context")
            return [0.0] * 1536
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
            # If we get here, we're in an event loop, so we can't use asyncio.run()
            print("Already in event loop, cannot use Copilot chat completion in this context")
            raise Exception("Cannot use Copilot chat in event loop context")
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(_create())
    except Exception as e:
        print(f"Error running async Copilot chat completion: {e}")
        raise