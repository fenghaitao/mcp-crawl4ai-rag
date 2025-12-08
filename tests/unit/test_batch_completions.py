"""
Unit tests for batch chat completions API.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBatchCompletions:
    """Test suite for batch chat completions."""
    
    def test_batch_completions_empty_list(self):
        """Test batch completions with empty input."""
        from server.utils import create_chat_completions_batch
        
        results = create_chat_completions_batch([])
        assert results == []
    
    @patch('server.utils.openai.chat.completions.create')
    def test_batch_completions_single_request(self, mock_create):
        """Test batch completions with single request."""
        from server.utils import create_chat_completions_batch
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(
            message=Mock(content="Paris", role="assistant"),
            finish_reason="stop"
        )]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15
        )
        mock_create.return_value = mock_response
        
        messages_list = [
            [{"role": "user", "content": "What is the capital of France?"}]
        ]
        
        results = create_chat_completions_batch(
            messages_list=messages_list,
            model="gpt-4o-mini"
        )
        
        assert len(results) == 1
        assert results[0]["choices"][0]["message"]["content"] == "Paris"
        assert results[0]["model"] == "gpt-4o-mini"
        assert results[0]["usage"]["total_tokens"] == 15
    
    @patch('server.utils.openai.chat.completions.create')
    def test_batch_completions_multiple_requests(self, mock_create):
        """Test batch completions with multiple requests."""
        from server.utils import create_chat_completions_batch
        
        # Mock OpenAI responses
        responses = ["Paris", "London", "Berlin"]
        
        def create_mock_response(content):
            mock_response = Mock()
            mock_response.choices = [Mock(
                message=Mock(content=content, role="assistant"),
                finish_reason="stop"
            )]
            mock_response.model = "gpt-4o-mini"
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
            return mock_response
        
        # Return different responses for each call
        mock_create.side_effect = [create_mock_response(r) for r in responses]
        
        messages_list = [
            [{"role": "user", "content": "Capital of France?"}],
            [{"role": "user", "content": "Capital of UK?"}],
            [{"role": "user", "content": "Capital of Germany?"}]
        ]
        
        results = create_chat_completions_batch(
            messages_list=messages_list,
            model="gpt-4o-mini",
            max_workers=3
        )
        
        assert len(results) == 3
        # Results should be in order
        assert results[0]["choices"][0]["message"]["content"] == "Paris"
        assert results[1]["choices"][0]["message"]["content"] == "London"
        assert results[2]["choices"][0]["message"]["content"] == "Berlin"
    
    @patch('server.utils.openai.chat.completions.create')
    def test_batch_completions_with_error(self, mock_create):
        """Test batch completions with one failing request."""
        from server.utils import create_chat_completions_batch
        
        # First call succeeds, second fails, third succeeds
        def side_effect(*args, **kwargs):
            if mock_create.call_count == 2:
                raise Exception("API Error")
            
            mock_response = Mock()
            mock_response.choices = [Mock(
                message=Mock(content="Success", role="assistant"),
                finish_reason="stop"
            )]
            mock_response.model = "gpt-4o-mini"
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
            return mock_response
        
        mock_create.side_effect = side_effect
        
        messages_list = [
            [{"role": "user", "content": "Question 1"}],
            [{"role": "user", "content": "Question 2"}],
            [{"role": "user", "content": "Question 3"}]
        ]
        
        results = create_chat_completions_batch(
            messages_list=messages_list,
            model="gpt-4o-mini",
            max_workers=3
        )
        
        assert len(results) == 3
        # First and third should succeed
        assert "error" not in results[0]
        assert results[0]["choices"][0]["message"]["content"] == "Success"
        
        # Second should have error
        assert "error" in results[1]
        assert "API Error" in results[1]["error"]
        
        # Third should succeed
        assert "error" not in results[2]
        assert results[2]["choices"][0]["message"]["content"] == "Success"
    
    def test_batch_completions_parameters(self):
        """Test that parameters are passed correctly."""
        from server.utils import create_chat_completions_batch
        
        with patch('server.utils.openai.chat.completions.create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(
                message=Mock(content="Test", role="assistant"),
                finish_reason="stop"
            )]
            mock_response.model = "gpt-4o"
            mock_response.usage = Mock(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )
            mock_create.return_value = mock_response
            
            messages_list = [
                [{"role": "user", "content": "Test"}]
            ]
            
            results = create_chat_completions_batch(
                messages_list=messages_list,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=500,
                max_workers=1
            )
            
            # Verify the call was made with correct parameters
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["temperature"] == 0.7
            assert call_kwargs["max_tokens"] == 500
    
    @patch('server.utils.os.getenv')
    @patch('server.utils.create_chat_completion_copilot')
    def test_batch_completions_uses_copilot(self, mock_copilot, mock_getenv):
        """Test that batch completions uses Copilot when configured."""
        from server.utils import create_chat_completions_batch
        
        # Configure to use Copilot
        def getenv_side_effect(key, default=None):
            if key == "USE_COPILOT_CHAT":
                return "true"
            elif key == "MODEL_CHOICE":
                return "gpt-4o"
            return default
        
        mock_getenv.side_effect = getenv_side_effect
        
        # Mock Copilot response
        mock_copilot.return_value = {
            "choices": [{
                "message": {
                    "content": "Copilot response",
                    "role": "assistant"
                },
                "finish_reason": "stop"
            }],
            "model": "gpt-4o",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        messages_list = [
            [{"role": "user", "content": "Test"}]
        ]
        
        results = create_chat_completions_batch(
            messages_list=messages_list,
            max_workers=1
        )
        
        # Verify Copilot was called
        assert mock_copilot.called
        assert len(results) == 1
        assert results[0]["choices"][0]["message"]["content"] == "Copilot response"


class TestCopilotBatchCompletions:
    """Test suite for Copilot-specific batch completions."""
    
    @pytest.mark.asyncio
    async def test_copilot_batch_empty_list(self):
        """Test Copilot batch with empty input."""
        from llms.copilot_client import CopilotClient
        
        client = CopilotClient()
        results = await client.create_chat_completions_batch([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_copilot_batch_multiple_requests(self):
        """Test Copilot batch with multiple requests."""
        from llms.copilot_client import CopilotClient
        
        client = CopilotClient()
        
        # Mock the single completion method
        async def mock_completion(messages, **kwargs):
            # Return different responses based on message content
            content = messages[0]["content"]
            return {
                "choices": [{
                    "message": {
                        "content": f"Response to: {content}",
                        "role": "assistant"
                    },
                    "finish_reason": "stop"
                }],
                "model": "gpt-4o",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15
                }
            }
        
        client.create_chat_completion = mock_completion
        
        messages_list = [
            [{"role": "user", "content": "Question 1"}],
            [{"role": "user", "content": "Question 2"}],
            [{"role": "user", "content": "Question 3"}]
        ]
        
        results = await client.create_chat_completions_batch(messages_list)
        
        assert len(results) == 3
        assert "Question 1" in results[0]["choices"][0]["message"]["content"]
        assert "Question 2" in results[1]["choices"][0]["message"]["content"]
        assert "Question 3" in results[2]["choices"][0]["message"]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
