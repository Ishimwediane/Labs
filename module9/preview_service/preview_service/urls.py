from django.urls import path
from preview.views import FetchPreviewView

urlpatterns = [
    path("fetch-preview/", FetchPreviewView.as_view(), name="fetch_preview"),
]
