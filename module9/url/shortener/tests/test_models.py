from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from shortener.models import Url, Tag
from accounts.models import User, UserTier
from datetime import timedelta

class UrlModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pwd", tier=UserTier.FREE)

    def test_url_expires_at_past_fails(self):
        url = Url(
            original_url="https://google.com",
            short_url="goog12",
            owner=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        with self.assertRaisesMessage(ValidationError, "Expiration datetime must be in the future."):
            url.clean()

    def test_url_internal_loop_fails(self):
        url = Url(
            original_url="http://localhost:8002/api/",
            short_url="loop12",
            owner=self.user
        )
        with self.assertRaisesMessage(ValidationError, "Cannot save internal URLs."):
            url.clean()

class TagModelTests(TestCase):
    def test_tag_lowercases_and_strips(self):
        tag = Tag(name="  UpperCaseTag  ")
        tag.clean()
        self.assertEqual(tag.name, "uppercasetag")
