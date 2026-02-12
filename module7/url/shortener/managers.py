from django.db import models
from django.utils import timezone

class URLQuerySet(models.QuerySet):
    def active_urls(self):
        return self.filter(is_active=True)
    
    def expired_urls(self):
        return self.filter(expires_at__lt=timezone.now())
    
    def popular_urls(self):
        return self.order_by('-click_count')