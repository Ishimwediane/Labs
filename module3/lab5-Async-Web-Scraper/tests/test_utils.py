"""Tests for utility functions and decorators."""

import asyncio
import pytest
from src.utils import retry, log_execution, async_response_generator, async_batch_processor


@pytest.mark.asyncio
async def test_retry_decorator_success():
    """Test that retry decorator works with successful async function."""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1)
    async def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await successful_function()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_decorator_eventual_success():
    """Test that retry decorator retries until success."""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1)
    async def eventually_successful():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"
    
    result = await eventually_successful()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_decorator_max_attempts():
    """Test that retry decorator fails after max attempts."""
    call_count = 0
    
    @retry(max_attempts=3, delay=0.1)
    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        await always_fails()
    
    assert call_count == 3


@pytest.mark.asyncio
async def test_log_execution_decorator():
    """Test that log_execution decorator works correctly."""
    
    @log_execution
    async def sample_function():
        await asyncio.sleep(0.1)
        return "completed"
    
    result = await sample_function()
    assert result == "completed"


@pytest.mark.asyncio
async def test_async_response_generator():
    """Test async response generator."""
    responses = [
        {"url": "http://example.com", "status": 200},
        {"url": "http://test.com", "status": 404},
    ]
    
    collected = []
    async for response in async_response_generator(responses):
        collected.append(response)
    
    assert len(collected) == 2
    assert collected == responses


@pytest.mark.asyncio
async def test_async_batch_processor():
    """Test async batch processor."""
    items = list(range(10))
    batches = []
    
    async for batch in async_batch_processor(items, batch_size=3):
        batches.append(batch)
    
    assert len(batches) == 4  # 3, 3, 3, 1
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]
