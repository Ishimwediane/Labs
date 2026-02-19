from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from shortener.models import Url, Tag
from django.conf import settings

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)
    
    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class UrlSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Url
        fields = ['id', 'original_url', 'short_url', 'short_link', 'created_at', 'click_count', 'is_active', 'expires_at', 'tags', 'custom_alias', 'title', 'description', 'favicon']
        read_only_fields = ['id', 'short_url', 'created_at', 'click_count']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_url}/'
