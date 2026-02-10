from django.contrib import admin
from .models import Url, Tag, Click

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('url', 'ip_address', 'country', 'created_at')
    list_filter = ('country', 'created_at')
    readonly_fields = ('url', 'ip_address', 'user_agent', 'country', 'city', 'referer')

@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'short_url', 'owner', 'click_count', 'is_active', 'expires_at')
    search_fields = ('original_url', 'short_url', 'owner__username')
    readonly_fields = ('short_url', 'click_count')
