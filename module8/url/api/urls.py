from django.urls import path
from .views import CreateShortUrlView, RedirectUrlView

urlpatterns = [
    path('api/urls/', CreateShortUrlView.as_view(), name='create_short_url'),
    path('<str:short_code>/', RedirectUrlView.as_view(), name='redirect_url'),
]
