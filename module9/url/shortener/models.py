from django.db import models
from django.conf import settings
from .managers import URLQuerySet
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.lower().strip()

    def __str__(self):
        return self.name


class Url(models.Model):
    original_url = models.URLField(max_length=2000)
    short_url = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='urls'
    )
    click_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='urls', blank=True)
    custom_alias = models.CharField(max_length=50, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    favicon = models.CharField(max_length=2000, null=True, blank=True)

    objects = URLQuerySet.as_manager()

    def clean(self):
        super().clean()
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError({'expires_at': "Expiration datetime must be in the future."})
            
        if self.original_url:
            if 'localhost' in self.original_url or '127.0.0.1' in self.original_url:
                raise ValidationError({'original_url': "Cannot save internal URLs."})

    def __str__(self):
        return self.short_url

    def get_clicks_by_country(self):
        """Returns a list of countries and their click counts for this URL."""
        return self.clicks.values('country').annotate(total=Count('id'))


class Click(models.Model):
    url = models.ForeignKey(Url, on_delete=models.CASCADE, related_name='clicks')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    referer = models.URLField(max_length=2000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} - {self.url.short_url}"
