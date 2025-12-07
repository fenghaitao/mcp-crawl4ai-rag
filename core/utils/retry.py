"""
Retry decorator for handling transient failures.
"""

import functools
import time
import logging
from typing import Type, Tuple, Callable, Any

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
):
    """
    Retry decorator for handling transient failures.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        exceptions: Exception types to retry on
        on_retry: Optional callback called on each retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Final attempt failed, re-raise
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = backoff_factor ** attempt
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def with_retry_logging(exception: Exception, attempt: int) -> None:
    """Default retry callback that logs retry attempts."""
    logger.info(f"Retry attempt #{attempt}: {type(exception).__name__}: {exception}")