from django.urls import path
from .views import (
    UrlListCreateView,
    UrlDetailView,
    RedirectUrlView,
    UrlAnalyticsView,
)

urlpatterns = [
    # List + Create
    path('api/urls/', UrlListCreateView.as_view(), name='url_list_create'),

    # Retrieve (GET) + Update (PUT) + Delete (DELETE) — all in UrlDetailView
    path('api/urls/<str:short_code>/', UrlDetailView.as_view(), name='url_detail'),

    # Analytics
    path('api/analytics/<str:short_code>/', UrlAnalyticsView.as_view(), name='url_analytics'),

    # Public redirect
    path('<str:short_code>/', RedirectUrlView.as_view(), name='redirect_url'),
]
