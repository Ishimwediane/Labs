from django.db import models
from rest_framework import serializers


class UrlSerializer(serializers.Serializer):
    original_url=serializers.URLField(max_length=2000)
    short_url=serializers.CharField(max_length=10,unique=True)
    created_at=serializers.DateTimeField(auto_now_add=True)
        
