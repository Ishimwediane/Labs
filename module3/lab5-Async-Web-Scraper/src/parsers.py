import re
from bs4 import BeautifulSoup
from .models import PageMetadata


def extract_metadata_from_html(html: str, url: str) -> PageMetadata:
    """
    Extract metadata from HTML content using BeautifulSoup and regex.
    
    Args:
        html: HTML content as string
        url: URL of the page
    
    Returns:
        PageMetadata object with extracted information
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract title
    title = None
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    # Extract description from meta tag
    description = None
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        description = meta_desc.get('content')
    
    # Alternative: use regex to find Open Graph description
    if not description:
        og_desc_match = re.search(
            r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )
        if og_desc_match:
            description = og_desc_match.group(1)
    
    return PageMetadata(url=url, title=title, description=description)
