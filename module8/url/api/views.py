from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from drf_spectacular.utils import extend_schema

from url.shortener.tasks import track_click_task

from .serializers import UrlSerializer, UrlCreateSerializer
from shortener.services import UrlShortenerService
from shortener.models import Url, Click

class CreateShortUrlView(APIView):
    @extend_schema(request=UrlCreateSerializer, responses={201: UrlSerializer})
    def post(self, request):
        serializer = UrlCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            url_obj = UrlShortenerService.create_short_url(
                original_url=serializer.validated_data["original_url"],
                owner=request.user,
                custom_alias=serializer.validated_data.get("custom_alias")
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        cache.set(f"url:{url_obj.short_url}", url_obj.original_url, timeout=None)
        return Response(
            UrlSerializer(url_obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class RedirectUrlView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(responses={302: None, 404: None})
    def get(self, request, short_code):
        cached_url = cache.get(f"url:{short_code}")
        if cached_url:
            try:
                url_obj = Url.objects.get(short_url=short_code)
                track_click_task.delay(url_obj.id, request.META.get("REMOTE_ADDR"), request.META.get("HTTP_USER_AGENT",""),request.META.get("HTTP_REFERER", ""))
                
            except Url.DoesNotExist:
                pass

            return redirect(cached_url)

        url_obj = get_object_or_404(
            Url.objects.select_related("owner"),
            short_url=short_code,
            is_active=True
        )
        
        cache.set(f"url:{short_code}", url_obj.original_url, timeout=None)

        track_click_task.delay(url_obj.id, request.META.get("REMOTE_ADDR"), request.META.get("HTTP_USER_AGENT",""),request.META.get("HTTP_REFERER", ""))
        

        return redirect(url_obj.original_url)

class UpdateShortUrlView(APIView):
    @extend_schema(request=UrlCreateSerializer, responses={200: UrlSerializer})
    def put(self, request, short_code):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        serializer = UrlCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_url =serializer.save()
        cache.delete(f"url:{update_url.short_url}")
        return Response(UrlSerializer(update_url,context={'request': request}).data, status=status.HTTP_200_OK)
