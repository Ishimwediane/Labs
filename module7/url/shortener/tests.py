from django.test import TestCase
from .models import Url
from .services import UrlShortenerService
from core.utils import generate_short_code

class UrlShortenerTests(TestCase):
    def test_generate_short_code(self):
        code = generate_short_code(6)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isalnum())

    def test_create_short_url(self):
        original_url = "https://www.google.com"
        url_obj = UrlShortenerService.create_short_url(original_url)
        self.assertEqual(url_obj.original_url, original_url)
        self.assertEqual(len(url_obj.short_url), 6)
        self.assertTrue(Url.objects.filter(short_url=url_obj.short_url).exists())

    def test_create_short_url_uniqueness(self):
        url1 = UrlShortenerService.create_short_url("https://example.com/1")
        url2 = UrlShortenerService.create_short_url("https://example.com/2")
        self.assertNotEqual(url1.short_url, url2.short_url)
