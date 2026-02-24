import httpx
from bs4 import BeautifulSoup


class MetadataExtractorService:

    @staticmethod
    def extract_metadata(url: str):
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            title = soup.title.string if soup.title else ""

            description_tag = soup.find("meta", attrs={"name": "description"})
            description = description_tag["content"] if description_tag else ""

            favicon_tag = soup.find("link", rel="icon")
            favicon = favicon_tag["href"] if favicon_tag else ""

            return {
                "title": title,
                "description": description,
                "favicon": favicon,
            }

        except Exception:
            return {
                "title": "",
                "description": "",
                "favicon": "",
            }