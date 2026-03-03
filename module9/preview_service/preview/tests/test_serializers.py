from rest_framework.test import APITestCase
from preview.serializers import PreviewRequestSerializer

class PreviewSerializerTests(APITestCase):

    def test_valid_http_url(self):
        data = {"url": "https://example.com"}
        serializer = PreviewRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_scheme_ftp(self):
        data = {"url": "ftp://example.com"}
        serializer = PreviewRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Only HTTP and HTTPS are supported.", str(serializer.errors['url'][0]))

    def test_ssrf_localhost_blocked(self):
        data = {"url": "http://localhost:8000/admin/"}
        serializer = PreviewRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Cannot scrape internal network addresses.", str(serializer.errors['url'][0]))

    def test_ssrf_127_blocked(self):
        data = {"url": "https://127.0.0.1/sensitive-data"}
        serializer = PreviewRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Cannot scrape internal network addresses.", str(serializer.errors['url'][0]))
