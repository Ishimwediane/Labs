import asyncio
import time
import logging
import aiohttp
from ..models import PageMetadata
from ..parsers import extract_metadata_from_html
from ..utils import retry, log_execution

logger = logging.getLogger(__name__)


@retry(max_attempts=3, delay=1.0)
@log_execution
async def fetch_url_async(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 10
) -> PageMetadata:
    """
    Asynchronously fetch a URL and extract metadata.
    
    Args:
        session: aiohttp ClientSession
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        PageMetadata object
    """
    start_time = time.perf_counter()
    metadata = PageMetadata(url=url)
    
    try:
        async with asyncio.wait_for(
            session.get(url),
            timeout=timeout
        ) as response:
            metadata.status_code = response.status
            metadata.fetch_time = time.perf_counter() - start_time
            
            if response.status == 200:
                html = await response.text()
                extracted = extract_metadata_from_html(html, url)
                metadata.title = extracted.title
                metadata.description = extracted.description
            else:
                metadata.error = f"HTTP {response.status}"
    except asyncio.TimeoutError:
        metadata.fetch_time = time.perf_counter() - start_time
        metadata.error = "Timeout"
        logger.error(f"Timeout fetching {url}")
    except Exception as e:
        metadata.fetch_time = time.perf_counter() - start_time
        metadata.error = str(e)
        logger.error(f"Error fetching {url}: {e}")
    
    return metadata


async def scrape_async(urls: list[str], max_concurrent: int = 10) -> list[PageMetadata]:
    """
    Scrape URLs asynchronously using asyncio and aiohttp.
    
    Args:
        urls: List of URLs to scrape
        max_concurrent: Maximum number of concurrent requests
    
    Returns:
        List of PageMetadata objects
    """
    logger.info(f"Starting async scraping of {len(urls)} URLs with max {max_concurrent} concurrent")
    start_time = time.perf_counter()
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(session: aiohttp.ClientSession, url: str) -> PageMetadata:
        async with semaphore:
            return await fetch_url_async(session, url)
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for all URLs
        tasks = [
            asyncio.create_task(fetch_with_semaphore(session, url))
            for url in urls
        ]
        
        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and convert to PageMetadata
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            final_results.append(
                PageMetadata(url=urls[i], error=str(result))
            )
        else:
            final_results.append(result)
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Async scraping completed in {elapsed:.2f}s")
    
    return final_results
