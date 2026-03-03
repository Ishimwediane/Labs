from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from shortener.models import Url, Click, Tag
from django.conf import settings
import re
from django.utils import timezone
from django.utils.html import strip_tags


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)
    custom_alias = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        if 'localhost' in value or '127.0.0.1' in value:
            raise serializers.ValidationError("Cannot shorten internal URLs.")
        return value

    def validate_custom_alias(self, value):
        if value:
            if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', value):
                raise serializers.ValidationError("Alias must be 3-50 characters long and contain only alphanumeric characters, hyphens, and underscores.")
            reserved = ['api', 'admin', 'login', 'register', 'auth', 'urls', 'analytics', 'swagger']
            if value.lower() in reserved:
                raise serializers.ValidationError(f"The alias '{value}' is reserved and cannot be used.")
            if Url.objects.filter(short_url=value).exists() or Url.objects.filter(custom_alias=value).exists():
                raise serializers.ValidationError("This alias is already in use.")
        return value


class UrlUpdateSerializer(serializers.ModelSerializer):
    """Used for PUT /api/urls/{short_code}/ — update target URL, optionally reset clicks."""
    reset_clicks = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Url
        fields = ['original_url', 'is_active', 'expires_at', 'reset_clicks', 'title', 'description']

    def validate_title(self, value):
        if value:
            return strip_tags(value)
        return value

    def validate_description(self, value):
        if value:
            return strip_tags(value)
        return value

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        return value

    def validate_original_url(self, value):
        if value:
            if not value.startswith(('http://', 'https://')):
                raise serializers.ValidationError("URL must start with http:// or https://")
            if 'localhost' in value or '127.0.0.1' in value:
                raise serializers.ValidationError("Cannot shorten internal URLs.")
        return value

    def update(self, instance, validated_data):
        reset = validated_data.pop('reset_clicks', False)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if reset:
            instance.click_count = 0
        instance.save()
        return instance


class UrlSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()
    click_count = serializers.IntegerField(read_only=True)
    detailed_stats = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Url
        fields = [
            'id', 'original_url', 'short_url', 'short_link',
            'click_count', 'detailed_stats', 'created_at',
            'tags', 'custom_alias', 'title', 'description', 'favicon',
            'is_active', 'expires_at',
        ]
        read_only_fields = ['id', 'short_url', 'created_at', 'click_count', 'detailed_stats']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_url}/'

    def get_detailed_stats(self, obj):
        """Only return click breakdown for Premium users."""
        request = self.context.get('request')
        if request and hasattr(request.user, 'is_premium') and request.user.is_premium:
            clicks = Click.objects.filter(url=obj)
            stats = {}
            for click in clicks:
                country = click.country or "Unknown"
                stats[country] = stats.get(country, 0) + 1
            return stats
        return None


class AnalyticsSerializer(serializers.Serializer):
    """Response schema for GET /api/analytics/{short_code}/"""
    url = serializers.CharField()
    total_clicks = serializers.IntegerField()
    clicks_by_country = serializers.ListField(child=serializers.DictField())
    recent_clicks = serializers.ListField(child=serializers.DictField(), required=False)
