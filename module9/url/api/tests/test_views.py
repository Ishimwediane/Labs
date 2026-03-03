from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from shortener.models import Url
from accounts.models import User, UserTier
from unittest.mock import patch

class ApiViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.free_user = User.objects.create_user(username="free", password="pwd", tier=UserTier.FREE)
        self.pro_user = User.objects.create_user(username="pro", password="pwd", is_premium=True, tier=UserTier.PRO)

    @patch('shortener.tasks.fetch_url_metadata_task.delay')
    def test_create_url_api_free_user_alias_fails(self, mock_fetch):
        self.client.force_authenticate(user=self.free_user)
        response = self.client.post("/api/v1/urls/", {
            "original_url": "https://example.com",
            "custom_alias": "free-alias"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Free users cannot set a custom alias", str(response.data))

    @patch('shortener.tasks.fetch_url_metadata_task.delay')
    def test_create_url_api_pro_user_success(self, mock_fetch):
        self.client.force_authenticate(user=self.pro_user)
        response = self.client.post("/api/v1/urls/", {
            "original_url": "https://example.com",
            "custom_alias": "pro-alias"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["short_url"], "pro-alias")
