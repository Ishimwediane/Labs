from .models import Url
from core.utils import generate_short_code

class UrlShortenerService:
    @staticmethod
    def create_short_url(original_url,owner,custom_alias=None):
        """
        create a short URL with business rules:
        free users:max 10 active URLs,cannot set custom alias
        premium users:unlimited active URLs,can set custom alias
        """
        if not owner.is_premium:
            active_urls_count = Url.objects.filter(owner=owner, is_active=True).count()
            if active_urls_count >= 10:
                raise ValueError("Free users can only create up to 10 active URLs.")
            if custom_alias:
                raise ValueError("Free users cannot set a custom alias.")
        short_code=custom_alias or generate_short_code()
        while Url.objects.filter(short_url=short_code).exists():
            short_code=generate_short_code()
        url=Url.objects.create(
            original_url=original_url,
            short_url=short_code,
            owner=owner
        )
        return url
    
    @staticmethod
    def get_url_by_short_code(short_code):
        try:
            return Url.objects.get(short_url=short_code, is_active=True)
        except Url.DoesNotExist:
            return None
        
    @staticmethod
    def delete_short_url(url_obj,user):
        if url_obj.owner != user:
            raise PermissionError("You do not have permission to delete this URL.")
        url_obj.delete()
        return True