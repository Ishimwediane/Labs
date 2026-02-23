from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, redirect
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import logging

from shortener.tasks import track_click_task
from shortener.services import UrlShortenerService
from shortener.models import Url, Tag
from .serializers import (
    UrlSerializer, UrlCreateSerializer,
    UrlUpdateSerializer, AnalyticsSerializer, TagSerializer,
)

logger = logging.getLogger(__name__)


# GET  /api/urls/          — list authenticated user's URLs
# POST /api/urls/          — create a new short URL

class UrlListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("tag", OpenApiTypes.STR, description="Filter by tag name"),
            OpenApiParameter("search", OpenApiTypes.STR, description="Search by original URL"),
            OpenApiParameter("page", OpenApiTypes.INT, description="Page number for pagination"),
        ],
        responses={200: UrlSerializer(many=True)},
    )
    def get(self, request):
        """List all URLs that belong to the authenticated user. Supports pagination and tag/search filtering."""
        queryset = (
            Url.objects.filter(owner=request.user)
            .select_related("owner")
            .prefetch_related("tags")
            .order_by("-created_at")
        )

        tag = request.query_params.get("tag")
        search = request.query_params.get("search")
        if tag:
            queryset = queryset.filter(tags__name__icontains=tag) #icontains means Case insensitive search.
        if search:
            queryset = queryset.filter(original_url__icontains=search)

        # Paginate
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = UrlSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(request=UrlCreateSerializer, responses={201: UrlSerializer})
    def post(self, request):
        """Create a short URL — business rules enforced by the service layer."""
        serializer = UrlCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            url_obj = UrlShortenerService.create_short_url(
                original_url=serializer.validated_data["original_url"],
                owner=request.user,
                custom_alias=serializer.validated_data.get("custom_alias"),
                tags=serializer.validated_data.get("tags"),
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

        # Warm the cache immediately after creation
        cache.set(f"url:{url_obj.short_url}",
            {"id": url_obj.id, "original_url": url_obj.original_url},
            timeout=None,
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
        return Response(
            UrlSerializer(url_obj, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )



# GET    /api/urls/{short_code}/  — retrieve a single URL
# PUT    /api/urls/{short_code}/  — update a URL
# DELETE /api/urls/{short_code}/  — soft-deactivate a URL

class UrlDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UrlSerializer})
    def get(self, request, short_code):
        """Retrieve a URL owned by the authenticated user."""
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)
        return Response(UrlSerializer(url_obj, context={"request": request}).data)

    @extend_schema(request=UrlUpdateSerializer, responses={200: UrlSerializer})
    def put(self, request, short_code):
        """
        Update URL fields. 
        """
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        serializer = UrlUpdateSerializer(data=request.data, partial=True) #User can update only some fields
        serializer.is_valid(raise_exception=True)

        # Hand validated data to the service — business rules live there
        updated = UrlShortenerService.update_url(url_obj, serializer.validated_data)

        # Invalidate stale cache entry
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
    def delete(self, request, short_code):
        """
        delete a URL (mark is_active=False).
        """
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        UrlShortenerService.deactivate_url(url_obj)
        cache.delete(f"url:{short_code}")

        logger.info(
            "URL deactivated and cache cleared",
            extra={
                "url_id": url_obj.id,
                "short_code": short_code,
                "user": request.user.username,
            },
        )
        return Response(status=status.HTTP_204_NO_CONTENT)



# GET /{short_code}/  — Public redirect (302) + async an
class RedirectUrlView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={302: None, 404: None})
    def get(self, request, short_code):
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        referer = request.META.get("HTTP_REFERER", "")

        cached_data = cache.get(f"url:{short_code}")

        if cached_data:
            logger.info(
                "Cache hit — redirecting from cache",
                extra={"short_code": short_code, "ip": ip},
            )
            track_click_task.delay(cached_data["id"], ip, user_agent, referer)
            return redirect(cached_data["original_url"])

        # Cache miss — fetch from the DB
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


# GET /api/analytics/{short_code}/  — Detailed analytics

class UrlAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AnalyticsSerializer})
    def get(self, request, short_code):

        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        # Authorization decision: only premium users see recent click list
        include_recent = hasattr(request.user, "is_premium") and request.user.is_premium

        stats = UrlShortenerService.get_click_stats(url_obj, include_recent=include_recent)

        response_data = {
            "url": url_obj.short_url,
            "total_clicks": url_obj.click_count,
            "clicks_by_country": stats["clicks_by_country"],
        }
        if include_recent:
            response_data["recent_clicks"] = stats["recent_clicks"]

        return Response(response_data)


# GET /api/tags/ — list all available tags
class TagListView(APIView):
    """Return all tag names available to assign to URLs."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: serializers.ListField(child=serializers.CharField())},
        summary="List available tags",
        description="Returns all tag names that can be assigned to URLs.",
        tags=["Tags"],
    )
    def get(self, request):
        tags = Tag.objects.all().order_by('name').values_list('name', flat=True)
        return Response(tags)
