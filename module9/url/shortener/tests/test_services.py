from django.test import TestCase
from shortener.services import UrlShortenerService
from shortener.models import Url
from accounts.models import User, UserTier
from unittest.mock import patch

class UrlShortenerServiceTests(TestCase):
    def setUp(self):
        self.free_user = User.objects.create_user(username="free", password="pwd", tier=UserTier.FREE)
        self.pro_user = User.objects.create_user(username="pro", password="pwd", is_premium=True, tier=UserTier.PRO)
        self.ent_user = User.objects.create_user(username="ent", password="pwd", is_premium=True, tier=UserTier.ENTERPRISE)

    @patch('shortener.tasks.fetch_url_metadata_task.delay')
    def test_free_user_limits(self, mock_fetch):
        # Free users cannot set custom alias
        with self.assertRaisesMessage(ValueError, "Free users cannot set a custom alias."):
            UrlShortenerService.create_short_url("https://example.com", self.free_user, custom_alias="myalias")
            
        # Free users capped at 10 URLs
        for i in range(10):
            UrlShortenerService.create_short_url(f"https://example.com/{i}", self.free_user)
            
        with self.assertRaisesMessage(ValueError, "Free users can only create up to 10 active URLs."):
            UrlShortenerService.create_short_url("https://example.com/11", self.free_user)

    @patch('shortener.tasks.fetch_url_metadata_task.delay')
    def test_pro_user_limits(self, mock_fetch):
        # Pro users can set custom alias
        url = UrlShortenerService.create_short_url("https://example.com", self.pro_user, custom_alias="pro-alias")
        self.assertEqual(url.short_url, "pro-alias")
        
        # Pro users capped at 50 URLs
        for i in range(49): # 1 already created
            UrlShortenerService.create_short_url(f"https://example.com/{i}", self.pro_user)
            
        with self.assertRaisesMessage(ValueError, "Pro users can only create up to 50 active URLs."):
            UrlShortenerService.create_short_url("https://example.com/51", self.pro_user)

    @patch('shortener.tasks.fetch_url_metadata_task.delay')
    def test_enterprise_user_limits(self, mock_fetch):
        # Enterprise users can set custom alias and have no limits
        url = UrlShortenerService.create_short_url("https://example.com", self.ent_user, custom_alias="ent-alias")
        self.assertEqual(url.short_url, "ent-alias")
        
        for i in range(55): # Surpass Pro limit
            UrlShortenerService.create_short_url(f"https://example.com/{i}", self.ent_user)
            
        count = Url.objects.filter(owner=self.ent_user).count()
        self.assertEqual(count, 56)
