from rest_framework import serializers
from .models import Url


class UrlCreateSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2000)
    
    def validate_original_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class UrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Url
        fields = ['id', 'original_url', 'short_url', 'created_at']
        read_only_fields = ['id', 'short_url', 'created_at']


