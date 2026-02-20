from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count, F
from django.core.cache import cache
from drf_spectacular.utils import extend_schema

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

        # Store both the id and original_url so cache hits can still log clicks
        cache.set(f"url:{url_obj.short_url}", {"id": url_obj.id, "original_url": url_obj.original_url}, timeout=None)
        return Response(
            UrlSerializer(url_obj, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class RedirectUrlView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(responses={302: None, 404: None})
    def get(self, request, short_code):
        cached_data = cache.get(f"url:{short_code}")

        country = request.META.get('HTTP_CF_IPCOUNTRY', 'Unknown')

        if cached_data:
            # CACHE HIT: redirect fast, but still log the click
            Click.objects.create(
                url_id=cached_data["id"],  # Use url_id 
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                referer=request.META.get("HTTP_REFERER"),
                country=country
            )
            # Atomic increment — no race condition, no need to fetch the object
            Url.objects.filter(id=cached_data["id"]).update(click_count=F("click_count") + 1)
            return redirect(cached_data["original_url"])

        # CACHE MISS: fetch from PostgreSQL, then cache it
        url_obj = get_object_or_404(
            Url.objects.select_related("owner"),
            short_url=short_code,
            is_active=True
        )

        Click.objects.create(
            url=url_obj,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referer=request.META.get("HTTP_REFERER"),
            country=country
        )

        url_obj.click_count += 1
        url_obj.save(update_fields=["click_count"])
        # Cache with dict so future cache hits have the id available
        cache.set(f"url:{short_code}", {"id": url_obj.id, "original_url": url_obj.original_url}, timeout=None)
        return redirect(url_obj.original_url)

class UserUrlsView(ListAPIView):
    serializer_class = UrlSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optimized query: select_related for owner, prefetch_related for tags
        return Url.objects.filter(owner=self.request.user).select_related('owner').prefetch_related('tags')

class UrlAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, short_code):
        url = get_object_or_404(Url, short_url=short_code, owner=request.user)
        
        # Aggregation: Total clicks per country
        clicks_by_country = Click.objects.filter(url=url).values('country').annotate(total_clicks=Count('id')).order_by('-total_clicks')
        
        return Response({
            "url": url.short_url,
            "clicks_by_country": clicks_by_country
        })
