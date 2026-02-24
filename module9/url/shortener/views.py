from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from url.shortener.models import Url
from .models import Url
from api.serializers import UrlSerializer, UrlCreateSerializer 
from rest_framework.permissions import IsAuthenticated 
from .permissions import IsOwnerOrReadOnly

# Create your views here.
class UrlViewSet(ModelViewSet):
    queryset = Url.objects.all()
    serializer_class = UrlSerializer
    permission_classes = [IsAuthenticated,IsOwnerOrReadOnly]