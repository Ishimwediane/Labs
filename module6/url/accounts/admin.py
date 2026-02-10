from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_premium', 'tier', 'is_staff')
    list_filter = ('is_premium', 'tier', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Premium Info', {'fields': ('is_premium', 'tier')}),
    )
