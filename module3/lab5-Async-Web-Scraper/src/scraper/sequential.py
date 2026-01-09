import time
import logging
from ..models import PageMetadata
from ..parsers import extract_metadata_from_html

logger = logging.getLogger(__name__)


def fetch_url_sync(url: str, timeout: int = 10) -> PageMetadata:
    """
    Synchronously fetch a URL and extract metadata.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
    
    Returns:
        PageMetadata object
    """
    import requests
    
    start_time = time.perf_counter()
    metadata = PageMetadata(url=url)
    
    try:
        response = requests.get(url, timeout=timeout)
        metadata.status_code = response.status_code
        metadata.fetch_time = time.perf_counter() - start_time
        
        if response.status_code == 200:
            extracted = extract_metadata_from_html(response.text, url)
            metadata.title = extracted.title
            metadata.description = extracted.description
        else:
            metadata.error = f"HTTP {response.status_code}"
    except Exception as e:
        metadata.fetch_time = time.perf_counter() - start_time
        metadata.error = str(e)
        logger.error(f"Error fetching {url}: {e}")
    
    return metadata


def scrape_sequential(urls: list[str]) -> list[PageMetadata]:
    """
    Scrape URLs sequentially (one at a time).
    
    Args:
        urls: List of URLs to scrape
    
    Returns:
        List of PageMetadata objects
    """
    logger.info(f"Starting sequential scraping of {len(urls)} URLs")
    start_time = time.perf_counter()
    
    results = []
    for url in urls:
        result = fetch_url_sync(url)
        results.append(result)
    
    elapsed = time.perf_counter() - start_time
    logger.info(f"Sequential scraping completed in {elapsed:.2f}s")
    
    return results
