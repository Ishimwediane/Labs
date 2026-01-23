from django.urls import path
from .views import CreateShortUrlView

urlpatterns = [
    path("shorten/", CreateShortUrlView.as_view(), name="create-short-url"),
]
