from rest_framework import serializers
from urllib.parse import urlparse

class PreviewRequestSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        parsed = urlparse(value)
        if parsed.scheme not in ['http', 'https']:
            raise serializers.ValidationError("Only HTTP and HTTPS are supported.")
        
        # Basic SSRF protection
        forbidden_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        if parsed.hostname in forbidden_hosts:
            raise serializers.ValidationError("Cannot scrape internal network addresses.")
            
        return value
