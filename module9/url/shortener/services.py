from django.db.models import Count, F
from .models import Url, Tag, Click
from core.utils import generate_short_code


class UrlShortenerService:

    @staticmethod
    def create_short_url(original_url, owner, custom_alias=None, tags=None):
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

        short_code = custom_alias or generate_short_code()
        
        # Ensure uniqueness
        while Url.objects.filter(short_url=short_code).exists():
            if custom_alias:
                raise ValueError(f"Alias '{custom_alias}' is already taken.")
            short_code = generate_short_code()

        url = Url.objects.create(
            original_url=original_url,
            short_url=short_code,
            owner=owner
        )

        if tags:
            UrlShortenerService.set_tags(url, tags)

        return url

    @staticmethod
    def update_url(url_obj, validated_data):
        """Apply updates and handle special flags like reset_clicks."""
        reset_clicks = validated_data.pop("reset_clicks", False)
        tag_names = validated_data.pop("tags", None)

        # Update standard fields
        for attr, value in validated_data.items():
            setattr(url_obj, attr, value)

        if reset_clicks:
            url_obj.click_count = 0

        url_obj.save()

        if tag_names is not None:
            UrlShortenerService.set_tags(url_obj, tag_names)

        return url_obj

    @staticmethod
    def deactivate_url(url_obj):
        """Soft-delete: mark a URL as inactive."""
        url_obj.is_active = False
        url_obj.save(update_fields=['is_active'])

    @staticmethod
    def set_tags(url_obj, tag_names):
        """Replace all tags on a URL with the given list of names."""
        tags = Tag.objects.filter(name__in=tag_names)
        url_obj.tags.set(tags)

    @staticmethod
    def get_url_by_short_code(short_code):
        """Return an active URL object by its short code, or None."""
        try:
            return Url.objects.get(short_url=short_code, is_active=True)
        except Url.DoesNotExist:
            return None

    @staticmethod
    def get_click_stats(url_obj, include_recent=False):
        """Aggregate click data for the dashboard/analytics."""
        total_clicks = url_obj.click_count

        # Aggregation by country
        clicks_by_country = list(
            Click.objects.filter(url=url_obj)
            .values("country")
            .annotate(total_clicks=Count("id"))
            .order_by("-total_clicks")
        )

        stats = {
            "total_clicks": total_clicks,
            "clicks_by_country": clicks_by_country,
        }

        if include_recent:
            recent = list(
                Click.objects.filter(url=url_obj)
                .order_by("-created_at")[:20]
                .values("ip_address", "country", "user_agent", "created_at")
            )
            stats["recent_clicks"] = recent

        return stats

    @staticmethod
    def delete_short_url(url_obj, user):
        """Hard delete (not used in default flow, but here for compatibility)."""
        if url_obj.owner != user:
            raise PermissionError("You do not have permission to delete this URL.")
        url_obj.delete()
        return True