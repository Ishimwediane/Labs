from dataclasses import dataclass
from typing import Optional


@dataclass
class PageMetadata:
    """Data class to store extracted page metadata."""
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    status_code: Optional[int] = None
    fetch_time: float = 0.0
    error: Optional[str] = None
