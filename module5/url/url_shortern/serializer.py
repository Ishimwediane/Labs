from rest_framework import serializers
from .models import Url

class UrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Url
        fields = ['original_url', 'short_url', 'created_at']
        read_only_fields = ['short_url', 'created_at'] 