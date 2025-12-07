"""
Tests for retry mechanism.
"""

import pytest
import time
from unittest.mock import Mock
from core.utils.retry import retry, with_retry_logging


class TestRetryMechanism:
    """Test retry decorator functionality."""
    
    def test_successful_execution_no_retry(self):
        """Test function that succeeds on first attempt."""
        
        @retry(max_attempts=3)
        def always_succeeds():
            return "success"
        
        result = always_succeeds()
        assert result == "success"
    
    def test_retry_on_exception(self):
        """Test retry behavior on exceptions."""
        attempt_count = 0
        
        @retry(max_attempts=3, backoff_factor=0.1)  # Fast retry for testing
        def fails_twice():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError(f"Attempt {attempt_count} failed")
            return f"success on attempt {attempt_count}"
        
        result = fails_twice()
        assert result == "success on attempt 3"
        assert attempt_count == 3
    
    def test_max_attempts_exceeded(self):
        """Test behavior when max attempts are exceeded."""
        
        @retry(max_attempts=2, backoff_factor=0.1)
        def always_fails():
            raise RuntimeError("Always fails")
        
        with pytest.raises(RuntimeError, match="Always fails"):
            always_fails()
    
    def test_specific_exceptions_only(self):
        """Test retry only on specific exception types."""
        
        @retry(max_attempts=3, exceptions=(ValueError,), backoff_factor=0.1)
        def fails_with_runtime_error():
            raise RuntimeError("Should not retry")
        
        # Should not retry on RuntimeError
        with pytest.raises(RuntimeError, match="Should not retry"):
            fails_with_runtime_error()
    
    def test_backoff_factor(self):
        """Test exponential backoff timing."""
        start_time = time.time()
        attempt_count = 0
        
        @retry(max_attempts=3, backoff_factor=0.1)  # Small backoff for testing
        def fails_with_timing():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError(f"Attempt {attempt_count}")
            return "success"
        
        result = fails_with_timing()
        elapsed = time.time() - start_time
        
        assert result == "success"
        # Should have some delay from backoff (0.1 + 0.2 = 0.3s minimum)
        assert elapsed > 0.25
    
    def test_retry_callback(self):
        """Test retry callback functionality."""
        callback_calls = []
        
        def test_callback(exception, attempt):
            callback_calls.append((str(exception), attempt))
        
        @retry(max_attempts=3, backoff_factor=0.1, on_retry=test_callback)
        def fails_twice():
            if len(callback_calls) < 2:
                raise ValueError(f"Fail {len(callback_calls) + 1}")
            return "success"
        
        result = fails_twice()
        assert result == "success"
        assert len(callback_calls) == 2
        assert callback_calls[0] == ("Fail 1", 1)
        assert callback_calls[1] == ("Fail 2", 2)
    
    def test_with_retry_logging(self):
        """Test the default retry logging callback."""
        # This is more of an integration test to ensure logging doesn't crash
        exception = ValueError("Test exception")
        
        # Should not raise any exceptions
        with_retry_logging(exception, 1)
        with_retry_logging(exception, 5)
    
    def test_zero_attempts_configuration(self):
        """Test edge case with zero max attempts."""
        
        @retry(max_attempts=0, backoff_factor=0.1)
        def should_not_run():
            return "should not execute"
        
        # Should raise immediately without running the function
        with pytest.raises(ValueError):  # or appropriate exception
            should_not_run()
    
    def test_preserve_function_metadata(self):
        """Test that retry decorator preserves function metadata."""
        
        @retry(max_attempts=3)
        def documented_function():
            """This function has documentation."""
            return "result"
        
        assert documented_function.__doc__ == "This function has documentation."
        assert documented_function.__name__ == "documented_function"