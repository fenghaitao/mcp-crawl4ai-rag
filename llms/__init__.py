"""
LLM clients package.

This package contains all LLM service clients including:
- iFlow/Qwen models via DashScope API
- GitHub Copilot API for embeddings and chat
- DashScope direct client
"""

from .iflow_client import create_chat_completion_iflow, test_iflow_connection
from .copilot_client import (
    create_embeddings_batch_copilot,
    create_embedding_copilot, 
    create_chat_completion_copilot,
    get_copilot_client
)

__all__ = [
    'create_chat_completion_iflow',
    'test_iflow_connection',
    'create_embeddings_batch_copilot', 
    'create_embedding_copilot',
    'create_chat_completion_copilot',
    'get_copilot_client'
]