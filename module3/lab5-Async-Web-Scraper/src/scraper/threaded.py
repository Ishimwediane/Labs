import time
import logging
from concurrent.futures import ThreadPoolExecutor
from ..models import PageMetadata
from .sequential import fetch_url_sync

logger = logging.getLogger(__name__)


def scrape_threaded(urls: list[str], max_workers: int = 5) -> list[PageMetadata]:
    """
    Scrape URLs using threading for concurrency.
    
    Args:
        urls: List of URLs to scrape
        max_workers: Maximum number of concurrent threads
    
    Returns:
        List of PageMetadata objects
    """
    logger.info(f"Starting threaded scraping of {len(urls)} URLs with {max_workers} workers")
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_url_sync, urls))
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Threaded scraping completed in {elapsed:.2f}s")
    
    return results
