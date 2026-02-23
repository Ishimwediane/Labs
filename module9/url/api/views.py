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
            queryset = queryset.filter(tags__name__icontains=tag)
        if search:
            queryset = queryset.filter(original_url__icontains=search)

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

        # Warm the cache
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
            },
        )
        return Response(
            UrlSerializer(url_obj, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class UrlDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UrlSerializer})
    def get(self, request, short_code):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)
        return Response(UrlSerializer(url_obj, context={"request": request}).data)

    @extend_schema(request=UrlUpdateSerializer, responses={200: UrlSerializer})
    def put(self, request, short_code):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)

        serializer = UrlUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = UrlShortenerService.update_url(url_obj, serializer.validated_data)
        
        # Clear cache on update
        cache.delete(f"url:{short_code}")

        logger.info(
            "URL updated successfully",
            extra={"url_id": updated.id, "short_code": short_code, "user": request.user.username},
        )
        return Response(UrlSerializer(updated, context={"request": request}).data)

    @extend_schema(responses={204: None})
    def delete(self, request, short_code):
        url_obj = get_object_or_404(Url, short_url=short_code, owner=request.user)
        UrlShortenerService.deactivate_url(url_obj)
        cache.delete(f"url:{short_code}")

        logger.info(
            "URL deactivated",
            extra={"url_id": url_obj.id, "short_code": short_code, "user": request.user.username},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RedirectUrlView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, short_code):
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        referer = request.META.get("HTTP_REFERER", "")

        cached_data = cache.get(f"url:{short_code}")
        if cached_data:
            track_click_task.delay(cached_data["id"], ip, user_agent, referer)
            return redirect(cached_data["original_url"])

        url_obj = UrlShortenerService.get_url_by_short_code(short_code)
        if not url_obj:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update cache
        cache.set(f"url:{short_code}",
            {"id": url_obj.id, "original_url": url_obj.original_url},
            timeout=None,
        )

        track_click_task.delay(url_obj.id, ip, user_agent, referer)
        return redirect(url_obj.original_url)


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
            "total_clicks": stats["total_clicks"],
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
