import httpx
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger("preview")


class MetadataExtractorService:

    @staticmethod
    def extract_metadata(url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            with httpx.Client(follow_redirects=True, timeout=10.0, headers=headers) as client:
                response = client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # title 
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("meta", property="og:title"):
                title = soup.find("meta", property="og:title")["content"].strip()

            # description
            description = ""
            description_tag = soup.find("meta", attrs={"name": "description"})
            if description_tag and description_tag.get("content"):
                description = description_tag["content"].strip()
            else:
                og_description_tag = soup.find("meta", property="og:description")
                if og_description_tag and og_description_tag.get("content"):
                    description = og_description_tag["content"].strip()

            # favicon
            favicon = ""
            # Try various icon link relations
            icon_tags = soup.find_all("link", rel=lambda x: x and any(s in x.lower() for s in ["icon", "shortcut icon", "apple-touch-icon"]))
            
            if icon_tags:
                icon_href = icon_tags[0].get("href")
                if icon_href:
                    favicon = urljoin(url, icon_href)
            
            # fallback to /favicon.ico if none found in HTML
            if not favicon:
                favicon = urljoin(url, "/favicon.ico")

            return {
                "title": title,
                "description": description,
                "favicon": favicon,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Network error fetching {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error extracting metadata for {url}: {str(e)}")
            
        return {
            "title": "",
            "description": "",
            "favicon": "",
        }