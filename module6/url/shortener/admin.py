from django.contrib import admin
from .models import Url

@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'short_url', 'owner', 'click_count', 'is_active', 'expires_at')
    search_fields = ('original_url', 'short_url', 'owner__username')
    readonly_fields = ('short_url', 'click_count')  
