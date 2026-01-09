"""Tests for scraper functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.scraper import (
    PageMetadata,
    extract_metadata_from_html,
    fetch_url_sync,
    scrape_sequential,
    scrape_async
)


def test_extract_metadata_from_html():
    """Test metadata extraction from HTML."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="This is a test page">
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    
    metadata = extract_metadata_from_html(html, "http://example.com")
    
    assert metadata.url == "http://example.com"
    assert metadata.title == "Test Page"
    assert metadata.description == "This is a test page"


def test_extract_metadata_with_og_description():
    """Test metadata extraction with Open Graph description."""
    html = """
    <html>
        <head>
            <title>OG Test</title>
            <meta property="og:description" content="Open Graph description">
        </head>
        <body></body>
    </html>
    """
    
    metadata = extract_metadata_from_html(html, "http://example.com")
    
    assert metadata.title == "OG Test"
    assert metadata.description == "Open Graph description"


def test_page_metadata_dataclass():
    """Test PageMetadata dataclass."""
    metadata = PageMetadata(
        url="http://example.com",
        title="Test",
        description="Description",
        status_code=200,
        fetch_time=1.5
    )
    
    assert metadata.url == "http://example.com"
    assert metadata.title == "Test"
    assert metadata.status_code == 200
    assert metadata.error is None


@patch('requests.get')
def test_fetch_url_sync_success(mock_get):
    """Test synchronous URL fetching with success."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><head><title>Test</title></head></html>"
    mock_get.return_value = mock_response
    
    result = fetch_url_sync("http://example.com")
    
    assert result.url == "http://example.com"
    assert result.status_code == 200
    assert result.title == "Test"
    assert result.error is None


@patch('requests.get')
def test_fetch_url_sync_error(mock_get):
    """Test synchronous URL fetching with error."""
    mock_get.side_effect = Exception("Connection error")
    
    result = fetch_url_sync("http://example.com")
    
    assert result.url == "http://example.com"
    assert result.error == "Connection error"


def test_scrape_sequential():
    """Test sequential scraping."""
    with patch('src.scrapers.sequential.fetch_url_sync') as mock_fetch:
        mock_fetch.return_value = PageMetadata(
            url="http://example.com",
            status_code=200,
            title="Test"
        )
        
        urls = ["http://example1.com", "http://example2.com"]
        results = scrape_sequential(urls)
        
        assert len(results) == 2
        assert mock_fetch.call_count == 2


@pytest.mark.asyncio
async def test_scrape_async():
    """Test async scraping."""
    urls = ["http://example1.com", "http://example2.com"]
    
    with patch('src.scrapers.async_scraper.aiohttp.ClientSession') as mock_session:
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><head><title>Test</title></head></html>")
        
        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        results = await scrape_async(urls, max_concurrent=2)
        
        assert len(results) == 2
