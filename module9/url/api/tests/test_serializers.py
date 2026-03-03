from django.test import TestCase
from api.serializers import UrlCreateSerializer, UrlUpdateSerializer
from shortener.models import Url
from accounts.models import User, UserTier

class ApiSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", tier=UserTier.PRO, is_premium=True)

    def test_url_create_serializer_valid(self):
        data = {"original_url": "https://example.com", "custom_alias": "my-alias"}
        serializer = UrlCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_url_create_serializer_internal_loop_fails(self):
        data = {"original_url": "http://127.0.0.1:8002/admin"}
        serializer = UrlCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("original_url", serializer.errors)

    def test_url_create_serializer_reserved_alias_fails(self):
        data = {"original_url": "https://example.com", "custom_alias": "api"}
        serializer = UrlCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("custom_alias", serializer.errors)

    def test_url_update_serializer_html_stripping(self):
        url = Url.objects.create(original_url="https://example.com", short_url="stripper", owner=self.user)
        data = {
            "title": "Clean <script>alert(1)</script> Title",
            "description": "<div>Dirty</div><br/>"
        }
        serializer = UrlUpdateSerializer(instance=url, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_instance = serializer.save()
        self.assertEqual(updated_instance.title, "Clean alert(1) Title")
        self.assertEqual(updated_instance.description, "Dirty")
