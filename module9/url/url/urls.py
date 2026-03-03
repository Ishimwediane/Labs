from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Swagger/OpenAPI Documentation
    path('api/schema/', SpectacularAPIView.as_view(versioning_class=None), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema', versioning_class=None), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema', versioning_class=None), name='redoc'),

    # Include the API app urls with dynamic versioning
    path('api/<version>/', include('api.urls')),
    
    # accounts app urls (Auth)
    path('api/<version>/auth/', include('accounts.urls')),
    
    # core app urls
    path('api/<version>/core/', include('core.urls')),
]
