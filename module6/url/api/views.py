from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from drf_spectacular.utils import extend_schema

from .serializers import UrlSerializer, UrlCreateSerializer
from shortener.services import UrlShortenerService
from shortener.models import Url, Click


class CreateShortUrlView(APIView):
    @extend_schema(
        request=UrlCreateSerializer,
        responses={201: UrlSerializer},
        description="Create a new shortened URL"
    )
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
        url_obj = UrlShortenerService.create_short_url(original_url=serializer.validated_data["original_url"],owner=request.user)

        cache.set(f"url:{url_obj.short_url}", url_obj.original_url, timeout=None)

        return Response(
            UrlSerializer(url_obj).data,
            status=status.HTTP_201_CREATED
        )


class RedirectUrlView(APIView):
    @extend_schema(
        responses={302: None, 404: None},
        description="Redirect to the original URL"
    )
    def get(self, request, short_code):

        cached_url = cache.get(f"url:{short_code}")

        if cached_url:
            return redirect(cached_url)

    
        url_obj = get_object_or_404(Url.objects.select_related("owner"),short_url=short_code,is_active=True)

        
        Click.objects.create(url=url_obj,ip_address=request.META.get("REMOTE_ADDR"),user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referer=request.META.get("HTTP_REFERER")
        )

        
        url_obj.click_count += 1
        url_obj.save(update_fields=["click_count"])

        cache.set(f"url:{short_code}", url_obj.original_url, timeout=None)

        return redirect(url_obj.original_url)
