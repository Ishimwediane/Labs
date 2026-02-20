from django.urls import path
from .views import CreateShortUrlView, RedirectUrlView, UserUrlsView, UrlAnalyticsView

urlpatterns = [
    path('api/urls/', CreateShortUrlView.as_view(), name='create_short_url'),
    path('api/urls/me/', UserUrlsView.as_view(), name='user_urls'),
    path('api/urls/<str:short_code>/analytics/', UrlAnalyticsView.as_view(), name='url_analytics'),
    path('<str:short_code>/', RedirectUrlView.as_view(), name='redirect_url'),
]
