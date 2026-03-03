from django.test import TestCase
from preview.services import MetadataExtractorService
from unittest.mock import patch, MagicMock
import httpx

class MetadataExtractorServiceTests(TestCase):

    @patch('httpx.Client.get')
    def test_extract_metadata_success(self, mock_get):
        # Mocking the HTTP response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head>
                <title>Mocked Title</title>
                <meta name="description" content="Mocked Description">
                <link rel="icon" href="/favicon.png">
            </head>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        metadata = MetadataExtractorService.extract_metadata("https://example.com")
        
        self.assertEqual(metadata["title"], "Mocked Title")
        self.assertEqual(metadata["description"], "Mocked Description")
        self.assertEqual(metadata["favicon"], "https://example.com/favicon.png")

    @patch('httpx.Client.get')
    def test_extract_metadata_http_error(self, mock_get):
        # Simulate a 404 block
        mock_get.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock(status_code=404))

        metadata = MetadataExtractorService.extract_metadata("https://example.com/notfound")
        
        # Service swallows error and returns empty defaults instead of crashing backend tasks
        self.assertEqual(metadata["title"], "")
        self.assertEqual(metadata["description"], "")
        self.assertEqual(metadata["favicon"], "")
