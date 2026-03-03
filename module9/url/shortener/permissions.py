from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.models import UserTier

class IsOwnerOrReadOnly(BasePermission):
    """
    allow only owner to write but all others read
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user

class IsProUserOrHigher(BasePermission):
    """
    Allows access only to users with Pro or Enterprise tiers.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.tier in [UserTier.PRO, UserTier.ENTERPRISE])

class IsEnterpriseUser(BasePermission):
    """
    Allows access only to Enterprise tier users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.tier == UserTier.ENTERPRISE)
    