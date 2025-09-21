"""Error handling and retry utilities."""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar
import httpx
from fastapi import HTTPException, status


class AppError(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    """Authentication related errors."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ThrottledError(AppError):
    """API throttling errors."""
    def __init__(self, message: str, retry_after: int):
        self.retry_after = retry_after
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS)


class ValidationError(AppError):
    """Data validation errors."""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


T = TypeVar("T")


async def with_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retry_on: tuple = (ThrottledError,),
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for delay after each attempt
        retry_on: Tuple of exceptions to retry on
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception encountered if all retries fail
    """
    attempt = 0
    delay = initial_delay
    last_error = None

    while attempt < max_attempts:
        try:
            return await func()
        except retry_on as e:
            attempt += 1
            last_error = e
            
            if attempt == max_attempts:
                raise

            # For throttling errors, use the server's retry-after if provided
            if isinstance(e, ThrottledError):
                delay = min(e.retry_after, max_delay)
            else:
                delay = min(delay * backoff_factor, max_delay)

            await asyncio.sleep(delay)

    raise last_error


async def handle_graph_response(response: httpx.Response) -> None:
    """
    Handle Microsoft Graph API response errors.
    
    Args:
        response: The httpx response to check
    
    Raises:
        AuthError: For authentication issues
        ThrottledError: For rate limiting
        AppError: For other API errors
    """
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise AuthError("Authentication failed or token expired")
    
    elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_after = int(response.headers.get("Retry-After", 60))
        raise ThrottledError(
            "Too many requests, please try again later",
            retry_after=retry_after
        )
    
    elif response.status_code >= 400:
        error_data = response.json()
        message = error_data.get("error", {}).get("message", "Unknown error")
        raise AppError(message, response.status_code)


def get_retry_after(headers: dict) -> Optional[int]:
    """
    Extract Retry-After value from response headers.
    
    Args:
        headers: Response headers
    
    Returns:
        Seconds to wait before retry, or None if not found
    """
    retry_after = headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        # Try parsing as integer seconds
        return int(retry_after)
    except ValueError:
        try:
            # Try parsing as HTTP date
            retry_date = datetime.strptime(
                retry_after, "%a, %d %b %Y %H:%M:%S GMT"
            )
            return int((retry_date - datetime.utcnow()).total_seconds())
        except ValueError:
            return None