from django.db import models
from django.conf import settings
from .managers import URLQuerySet
from django.db.models import Count #  aggregation



class Tag(models.Model):
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Url(models.Model):
    original_url = models.URLField(max_length=2000)
    short_url = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='urls')
    click_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    tags=models.ManyToManyField(Tag,related_name='urls',blank=True)
    
    #query set
    objects=URLQuerySet.as_manager()
    
    def __str__(self):
        return self.short_url

    def get_clicks_by_country(self):
        """
        Returns a list of countries and their click counts for this URL.
        
        """
        return self.clicks.values('country').annotate(total=Count('id'))


class Click(models.Model):
    url=models.ForeignKey(Url,on_delete=models.CASCADE,related_name='clicks')
    ip_address=models.GenericIPAddressField()
    user_agent=models.TextField()
    country=models.CharField(max_length=100,blank=True,null=True)
    city=models.CharField(max_length=100,blank=True,null=True)
    referer=models.URLField(max_length=2000,blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.ip_address} - {self.url.short_url}"



    


