from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
import logging

from shortener.tasks import track_click_task

from .serializers import UrlSerializer, UrlCreateSerializer
from shortener.services import UrlShortenerService
from shortener.models import Url, Click

# Logger for API operations
logger = logging.getLogger(__name__)

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
            
            # Log successful URL creation
            logger.info(
                "URL created successfully",
                extra={
                    "url_id": url_obj.id,
                    "short_code": url_obj.short_url,
                    "user": request.user.username,
                    "is_custom": bool(serializer.validated_data.get("custom_alias"))
                }
            )
            
        except ValueError as e:
            # Log URL creation failure
            logger.warning(
                "URL creation failed",
                extra={
                    "user": request.user.username,
                    "error": str(e),
                    "original_url": serializer.validated_data.get("original_url")
                }
            )
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
            # Log cache hit
            logger.info(
                "Cache hit - redirecting from cache",
                extra={
                    "short_code": short_code,
                    "ip": request.META.get("REMOTE_ADDR")
                }
            )
            
            try:
                url_obj = Url.objects.get(short_url=short_code)
                track_click_task.delay(url_obj.id, request.META.get("REMOTE_ADDR"), request.META.get("HTTP_USER_AGENT",""),request.META.get("HTTP_REFERER", ""))
                
            except Url.DoesNotExist:
                pass

            return redirect(cached_url)

        # Log cache miss
        logger.info(
            "Cache miss - fetching from database",
            extra={"short_code": short_code}
        )
        
        url_obj = get_object_or_404(
            Url.objects.select_related("owner"),
            short_url=short_code,
            is_active=True
        )
        
        cache.set(f"url:{short_code}", url_obj.original_url, timeout=None)

        track_click_task.delay(url_obj.id, request.META.get("REMOTE_ADDR"), request.META.get("HTTP_USER_AGENT",""),request.META.get("HTTP_REFERER", ""))
        
        # Log redirect event
        logger.info(
            "Redirecting to original URL",
            extra={
                "short_code": short_code,
                "url_id": url_obj.id,
                "owner": url_obj.owner.username
            }
        )

        return redirect(url_obj.original_url)

class UpdateShortUrlView(APIView):
    @extend_schema(request=UrlCreateSerializer, responses={200: UrlSerializer})
    def put(self, request, short_code):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        serializer = UrlCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_url = serializer.save()
        
        # Invalidate cache
        cache.delete(f"url:{update_url.short_url}")
        
        # Log URL update
        logger.info(
            "URL updated and cache invalidated",
            extra={
                "url_id": update_url.id,
                "short_code": update_url.short_url,
                "user": request.user.username
            }
        )
        
        return Response(UrlSerializer(update_url,context={'request': request}).data, status=status.HTTP_200_OK)
