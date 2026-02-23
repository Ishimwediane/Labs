from rest_framework import serializers


class PreviewRequestSerializer(serializers.Serializer):
    url = serializers.URLField()
