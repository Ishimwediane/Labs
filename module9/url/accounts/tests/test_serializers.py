from django.test import TestCase
from accounts.serializers import RegisterSerializer
from accounts.models import User

class RegisterSerializerTests(TestCase):
    
    def test_valid_registration(self):
        data = {
            "username": "tester_123",
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "is_premium": False
        }
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_password_mismatch(self):
        data = {
            "username": "tester_123",
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "WrongPassword123!"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        
    def test_weak_password_length(self):
        data = {
            "username": "tester",
            "email": "test@example.com",
            "password": "Short!",
            "password_confirm": "Short!"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
        self.assertEqual(str(serializer.errors['password'][0]), "Password must be at least 8 characters long.")
        
    def test_invalid_username_characters(self):
        data = {
            "username": "invalid username space",
            "email": "test@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("username", serializer.errors)
        
    def test_duplicate_email(self):
        User.objects.create_user(username="first", email="duplicate@example.com", password="StrongPassword123!")
        data = {
            "username": "second",
            "email": "duplicate@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
