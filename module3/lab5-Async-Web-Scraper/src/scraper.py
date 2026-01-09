"""
Core scraper module - Re-exports for backward compatibility.

This module maintains backward compatibility with existing code and tests
by re-exporting all scraper functionality from the new modular structure.
"""

from .models import PageMetadata
from .parsers import extract_metadata_from_html
from .scrapers import (
    scrape_sequential,
    scrape_threaded,
    scrape_async,
    fetch_url_sync,
    fetch_url_async
)

__all__ = [
    'PageMetadata',
    'extract_metadata_from_html',
    'scrape_sequential',
    'scrape_threaded',
    'scrape_async',
    'fetch_url_sync',
    'fetch_url_async'
]
