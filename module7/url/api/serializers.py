from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from shortener.models import Url, Click
from django.conf import settings

class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)
    custom_alias = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class UrlSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()
    click_count = serializers.IntegerField(source='click_count', read_only=True)
    detailed_stats = serializers.SerializerMethodField()

    class Meta:
        model = Url
        fields = ['id', 'original_url', 'short_url', 'short_link', 'click_count', 'detailed_stats', 'created_at']
        read_only_fields = ['id', 'short_url', 'created_at', 'click_count', 'detailed_stats']

    @extend_schema_field(serializers.URLField())
    def get_short_link(self, obj):
        base_url = settings.BASE_URL.rstrip('/')
        return f'{base_url}/{obj.short_url}/'

    def get_detailed_stats(self, obj):
        # Only return analytics for Premium users
        request = self.context.get('request')
        if request and request.user.is_premium:
            clicks = Click.objects.filter(url=obj)
            stats = {}
            for click in clicks:
                country = click.country or "Unknown"
                stats[country] = stats.get(country, 0) + 1
            return stats
        return None
