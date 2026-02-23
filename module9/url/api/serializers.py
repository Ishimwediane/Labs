from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from shortener.models import Url, Tag
from django.conf import settings


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class UrlCreateSerializer(serializers.Serializer):
    """Input schema for POST /api/urls/ — validates fields only, no DB calls."""
    original_url = serializers.URLField(max_length=2000)
    custom_alias = serializers.CharField(max_length=50, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="List of tag names to assign e.g. ['Marketing', 'Social Media']"
    )

    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value

    def validate_tags(self, value):
        """Verify every tag name exists in the database."""
        valid_names = set(Tag.objects.values_list('name', flat=True))
        bad = [t for t in value if t not in valid_names]
        if bad:
            raise serializers.ValidationError(
                f"Unknown tag(s): {bad}. Available: {sorted(valid_names)}"
            )
        return value


class UrlUpdateSerializer(serializers.Serializer):
    """
    Input schema for PUT /api/urls/{short_code}/ 
    """
    original_url = serializers.URLField(max_length=2000, required=False)
    is_active = serializers.BooleanField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    reset_clicks = serializers.BooleanField(required=False, default=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        help_text="Replaces all tags on the URL. Pass [] to remove all tags."
    )

    def validate_tags(self, value):
        """Verify every tag name exists in the database."""
        valid_names = set(Tag.objects.values_list('name', flat=True))
        bad_tags = [t for t in value if t not in valid_names]
        if bad_tags:
            raise serializers.ValidationError(
                f"Unknown tag(s): {bad_tags}. Available: {sorted(valid_names)}"
            )
        return value


class UrlSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a Url instance.
    """
    short_link = serializers.SerializerMethodField()
    click_count = serializers.IntegerField(read_only=True)
    detailed_stats = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')

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
        return self.context.get('detailed_stats')


class AnalyticsSerializer(serializers.Serializer):
    """Response schema for GET /api/analytics/{short_code}/"""
    url = serializers.CharField()
    total_clicks = serializers.IntegerField()
    clicks_by_country = serializers.ListField(child=serializers.DictField())
    recent_clicks = serializers.ListField(child=serializers.DictField(), required=False)
