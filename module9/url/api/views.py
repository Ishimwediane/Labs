from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count, F
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging

from shortener.tasks import track_click_task
from .serializers import (
    UrlSerializer, UrlCreateSerializer,
    UrlUpdateSerializer, AnalyticsSerializer,
)
from shortener.services import UrlShortenerService
from shortener.models import Url, Click

logger = logging.getLogger(__name__)


class UrlListCreateView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter("tag", OpenApiTypes.STR, description="Filter by tag name"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by original URL"),
        ],
        responses={200: UrlSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        """GET /api/urls/ — list the authenticated user's URLs."""
        url_queryset = (
            Url.objects.filter(owner=request.user)
            .select_related("owner")
            .prefetch_related("tags")
        )
        tag = request.query_params.get("tag")
        search = request.query_params.get("search")
        if tag:
            url_queryset = url_queryset.filter(tags__name__icontains=tag)
        if search:
            url_queryset = url_queryset.filter(original_url__icontains=search)
        serializer = UrlSerializer(url_queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @extend_schema(request=UrlCreateSerializer, responses={201: UrlSerializer})
    def post(self, request, *args, **kwargs):
        serializer = UrlCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            url_obj = UrlShortenerService.create_short_url(
                original_url=serializer.validated_data["original_url"],
                owner=request.user,
                custom_alias=serializer.validated_data.get("custom_alias"),
            )
            logger.info(
                "URL created successfully",
                extra={
                    "url_id": url_obj.id,
                    "short_code": url_obj.short_url,
                    "user": request.user.username,
                    "is_custom": bool(serializer.validated_data.get("custom_alias")),
                },
            )
        except ValueError as e:
            logger.warning(
                "URL creation failed",
                extra={
                    "user": request.user.username,
                    "error": str(e),
                    "original_url": serializer.validated_data.get("original_url"),
                },
            )
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

      
        cache.set(
            f"url:{url_obj.short_url}",
            {"id": url_obj.id, "original_url": url_obj.original_url},
            timeout=None,
        )
        return Response(
            UrlSerializer(url_obj, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )




class UrlDetailView(APIView):
    @extend_schema(responses={200: UrlSerializer})
    def get(self, request, short_code, *args, **kwargs):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)
        return Response(
            UrlSerializer(url_obj, context={"request": request}).data
        )

    @extend_schema(request=UrlUpdateSerializer, responses={200: UrlSerializer})
    def put(self, request, short_code, *args, **kwargs):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        serializer = UrlUpdateSerializer(url_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()

        
        cache.delete(f"url:{short_code}")

        logger.info(
            "URL updated and cache invalidated",
            extra={
                "url_id": updated.id,
                "short_code": updated.short_url,
                "user": request.user.username,
            },
        )
        return Response(
            UrlSerializer(updated, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(responses={204: None})
    def delete(self, request, short_code, *args, **kwargs):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        
        url_obj.is_active = False
        url_obj.save(update_fields=["is_active"])

        
        cache.delete(f"url:{short_code}")

        logger.info(
            "URL deactivated and cache cleared",
            extra={"url_id": url_obj.id, "short_code": short_code, "user": request.user.username},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# GET /{short_code}/  — Public redirect (302) + async analytics + Redis cache
class RedirectUrlView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={302: None, 404: None})
    def get(self, request, short_code, *args, **kwargs):
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        referer = request.META.get("HTTP_REFERER", "")

        cached_data = cache.get(f"url:{short_code}")

        if cached_data:
            # CACHE HIT 
            logger.info(
                "Cache hit — redirecting from cache",
                extra={"short_code": short_code, "ip": ip},
            )
            track_click_task.delay(cached_data["id"], ip, user_agent, referer)
            return redirect(cached_data["original_url"])

        # CACHE MISS — fetch from PostgreSQL
        logger.info("Cache miss — fetching from database", extra={"short_code": short_code})

        url_obj = get_object_or_404(
            Url.objects.select_related("owner"),
            short_url=short_code,
            is_active=True,
        )

        cache.set(
            f"url:{short_code}",
            {"id": url_obj.id, "original_url": url_obj.original_url},
            timeout=None,
        )

        track_click_task.delay(url_obj.id, ip, user_agent, referer)

        logger.info(
            "Redirecting to original URL",
            extra={
                "short_code": short_code,
                "url_id": url_obj.id,
                "owner": url_obj.owner.username,
            },
        )
        return redirect(url_obj.original_url)


# GET /api/analytics/{short_code}/  — Detailed analytics (Premium only)

class UrlAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AnalyticsSerializer})
    def get(self, request, short_code, *args, **kwargs):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        total_clicks = url_obj.click_count

        # Clicks grouped by country
        clicks_by_country = list(
            Click.objects.filter(url=url_obj)
            .values("country")
            .annotate(total_clicks=Count("id"))
            .order_by("-total_clicks")
        )

        response_data = {
            "url": url_obj.short_url,
            "total_clicks": total_clicks,
            "clicks_by_country": clicks_by_country,
        }

        # Premium users also get recent click time-series
        if hasattr(request.user, "is_premium") and request.user.is_premium:
            recent = list(
                Click.objects.filter(url=url_obj)
                .order_by("-created_at")[:20]
                .values("ip_address", "country", "user_agent", "created_at")
            )
            response_data["recent_clicks"] = recent

        return Response(response_data)
