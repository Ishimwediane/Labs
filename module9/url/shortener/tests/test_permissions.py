from django.test import TestCase, RequestFactory
from shortener.permissions import IsProUserOrHigher, IsEnterpriseUser
from accounts.models import User, UserTier
from django.contrib.auth.models import AnonymousUser

class PermissionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.free_user = User.objects.create_user(username="free", tier=UserTier.FREE)
        self.pro_user = User.objects.create_user(username="pro", is_premium=True, tier=UserTier.PRO)
        self.ent_user = User.objects.create_user(username="ent", is_premium=True, tier=UserTier.ENTERPRISE)

    def test_is_pro_user_or_higher(self):
        permission = IsProUserOrHigher()
        
        request = self.factory.get('/')
        request.user = self.free_user
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = self.pro_user
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = self.ent_user
        self.assertTrue(permission.has_permission(request, None))
        
        request.user = AnonymousUser()
        self.assertFalse(permission.has_permission(request, None))

    def test_is_enterprise_user(self):
        permission = IsEnterpriseUser()
        
        request = self.factory.get('/')
        request.user = self.free_user
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = self.pro_user
        self.assertFalse(permission.has_permission(request, None))
        
        request.user = self.ent_user
        self.assertTrue(permission.has_permission(request, None))
