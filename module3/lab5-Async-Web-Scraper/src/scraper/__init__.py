from scraper.sequential import scrape_sequential, fetch_url_sync
from scraper.threaded import scrape_threaded
from scraper.async_scraper import scrape_async, fetch_url_async

__all__ = [
    'scrape_sequential',
    'fetch_url_sync',
    'scrape_threaded',
    'scrape_async',
    'fetch_url_async'
]
