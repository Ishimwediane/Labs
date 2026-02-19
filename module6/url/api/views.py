from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from drf_spectacular.utils import extend_schema

from .serializers import UrlSerializer, UrlCreateSerializer
from shortener.services import UrlShortenerService
from shortener.models import Url, Click


class CreateShortUrlView(APIView):
    permission_classes = [IsAuthenticated]

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
     
        url_obj = get_object_or_404(Url.objects.select_related("owner"),short_url=short_code,is_active=True)


        country = request.META.get('HTTP_CF_IPCOUNTRY') # Cloudflare header example
        if not country:
            country = "Unknown"

        Click.objects.create(url=url_obj,ip_address=request.META.get("REMOTE_ADDR"),user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referer=request.META.get("HTTP_REFERER"),
            country=country
        )

        
        url_obj.click_count += 1
        url_obj.save(update_fields=["click_count"])

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
