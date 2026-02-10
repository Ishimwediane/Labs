from .models import Url
from core.utils import generate_short_code

class UrlShortenerService:
    @staticmethod
    def create_short_url(original_url):
        while True:
            short_code = generate_short_code()
            if not Url.objects.filter(short_url=short_code).exists():
                break

        return Url.objects.create(
            original_url=original_url,
            short_url=short_code
        )
