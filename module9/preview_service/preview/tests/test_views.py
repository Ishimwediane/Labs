from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch

class PreviewViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('preview.services.MetadataExtractorService.extract_metadata')
    def test_fetch_preview_success(self, mock_extract):
        mock_extract.return_value = {
            "title": "Mock Title",
            "description": "Mock Desc",
            "favicon": "mock.ico"
        }

        response = self.client.post("/fetch-preview/", {"url": "https://example.com"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Mock Title")
        self.assertEqual(response.data["description"], "Mock Desc")

    def test_fetch_preview_invalid_url(self):
        response = self.client.post("/fetch-preview/", {"url": "not-a-url"})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("url", response.data)
