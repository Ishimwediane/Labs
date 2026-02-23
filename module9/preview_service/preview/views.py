from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PreviewRequestSerializer
from .services import MetadataExtractorService


class PreviewView(APIView):

    def post(self, request):
        serializer = PreviewRequestSerializer(data=request.data)

        if serializer.is_valid():
            url = serializer.validated_data["url"]

            metadata = MetadataExtractorService.extract_metadata(url)

            return Response(metadata, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)