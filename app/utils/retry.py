"""Retry utilities with exponential backoff"""
import asyncio
import logging
from typing import Callable, TypeVar, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_async(
    func: Callable[..., T],
    max_retries: int = 3,
    backoff_base: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        backoff_base: Base for exponential backoff (2.0 = 1s, 2s, 4s, ...)
        exceptions: Tuple of exceptions to catch and retry
        *args, **kwargs: Arguments to pass to func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = backoff_base ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
    
    raise last_exception


def retry_sync(
    func: Callable[..., T],
    max_retries: int = 3,
    backoff_base: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs
) -> T:
    """
    Retry a synchronous function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        backoff_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
        *args, **kwargs: Arguments to pass to func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all retries fail
    """
    import time
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = backoff_base ** attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {wait_time:.2f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
    
    raise last_exception


def with_timeout(timeout: float):
    """
    Decorator to add timeout to async functions
    
    Args:
        timeout: Timeout in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout}s")
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
        return wrapper
    return decorator

