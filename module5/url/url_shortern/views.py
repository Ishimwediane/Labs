from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializer import UrlSerializer
from .services import UrlShortenerService


class CreateShortUrlView(APIView):

    def post(self, request):
        serializer = UrlSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        original_url = serializer.validated_data['original_url']

        url_obj = UrlShortenerService.create_short_url(original_url)

        response_data = {
            "original_url": url_obj.original_url,
            "short_url": url_obj.short_url,
            "created_at": url_obj.created_at
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
