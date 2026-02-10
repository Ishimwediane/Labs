from django.contrib import admin
from .models import Url

@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ('original_url', 'short_url', 'created_at')
    search_fields = ('original_url', 'short_url')
    ordering = ('-created_at',)
