from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User, UserTier

class UserModelTests(TestCase):
    
    def test_create_regular_user(self):
        user = User.objects.create_user(
            username="normaluser",
            password="Password123!",
            is_premium=False,
            tier=UserTier.FREE
        )
        self.assertEqual(user.tier, UserTier.FREE)
        self.assertFalse(user.is_premium)
        
    def test_create_enterprise_user(self):
        user = User.objects.create_user(
            username="entuser",
            password="Password123!",
            is_premium=True,
            tier=UserTier.ENTERPRISE
        )
        self.assertEqual(user.tier, UserTier.ENTERPRISE)
        self.assertTrue(user.is_premium)
        
    def test_tier_sync_clean_method_premium_fails(self):
        """Testing the clean method intercepts bad tier mismatches."""
        user = User(
            username="baduser",
            password="Password123!",
            is_premium=True,
            tier=UserTier.FREE
        )
        with self.assertRaisesMessage(ValidationError, "A premium user cannot have a 'free' tier."):
            user.clean()
            
    def test_tier_sync_clean_method_free_fails(self):
        user = User(
            username="baduser2",
            password="Password123!",
            is_premium=False,
            tier=UserTier.PRO
        )
        with self.assertRaisesMessage(ValidationError, "A non-premium user must be on the 'free' tier."):
            user.clean()
