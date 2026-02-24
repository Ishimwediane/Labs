from django.urls import path
from preview.views import PreviewView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("fetch-preview/", PreviewView.as_view(), name="fetch_preview"),
    
    # Swagger/OpenAPI Documentation for Preview Service
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
