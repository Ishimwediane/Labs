import asyncio
import time
from functools import wraps
from typing import AsyncGenerator, Callable, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry async functions on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries
    
    Usage:
        @retry(max_attempts=3, delay=2.0)
        async def fetch_url(url):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log execution time of async functions.
    
    Usage:
        @log_execution
        async def process_data():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        logger.info(f"Starting execution of {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}")
            raise
    
    return wrapper


async def async_response_generator(
    responses: list[dict]
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields responses one at a time.
    
    Args:
        responses: List of response dictionaries
    
    Yields:
        Individual response dictionaries
    
    Usage:
        async for response in async_response_generator(responses):
            process(response)
    """
    for response in responses:
        # Simulate async processing
        await asyncio.sleep(0)
        yield response


async def async_batch_processor(
    items: list[Any],
    batch_size: int = 5
) -> AsyncGenerator[list[Any], None]:
    """
    Async generator that yields items in batches.
    
    Args:
        items: List of items to process
        batch_size: Number of items per batch
    
    Yields:
        Batches of items
    
    Usage:
        async for batch in async_batch_processor(urls, batch_size=10):
            await process_batch(batch)
    """
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        await asyncio.sleep(0)  # Yield control to event loop
        yield batch
