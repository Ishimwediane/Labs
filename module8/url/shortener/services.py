from django.db.models import Count
from .models import Url, Tag, Click
from core.utils import generate_short_code


class UrlShortenerService:

    @staticmethod
    def create_short_url(original_url, owner, custom_alias=None, tags=None):
        """
        Create a short URL with business rules:
          - Free users: max 10 active URLs, cannot set custom alias
          - Premium users: unlimited active URLs, can set custom alias
        Optionally assign a list of tag names.
        """
        if not owner.is_premium:
            active_count = Url.objects.filter(owner=owner, is_active=True).count()
            if active_count >= 10:
                raise ValueError("Free users can only create up to 10 active URLs.")
            if custom_alias:
                raise ValueError("Free users cannot set a custom alias.")

        short_code = custom_alias or generate_short_code()
        while Url.objects.filter(short_url=short_code).exists():
            short_code = generate_short_code()

        url = Url.objects.create(
            original_url=original_url,
            short_url=short_code,
            owner=owner,
        )

        if tags:
            UrlShortenerService.set_tags(url, tags)

        return url

    @staticmethod
    def update_url(instance, validated_data):
        """
        Apply field updates to a URL instance.
        Business rule: if reset_clicks=True, zero the click counter.
        If tags list is provided, replace all current tags.
        Ownership check must be done by the caller (view).
        """
        reset = validated_data.pop('reset_clicks', False)
        tag_names = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if reset:
            instance.click_count = 0
        instance.save()

        if tag_names is not None:
            UrlShortenerService.set_tags(instance, tag_names)

        return instance

    @staticmethod
    def deactivate_url(url_obj):
        """
        Soft-delete: mark a URL as inactive.
        Ownership check must be done by the caller (view).
        """
        url_obj.is_active = False
        url_obj.save(update_fields=['is_active'])

    @staticmethod
    def set_tags(url_obj, tag_names):
        """
        Replace all tags on a URL with the given list of tag names.
        Pass an empty list [] to remove all tags.
        Only accepts tag names that already exist in the Tag table.
        """
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
    def delete_short_url(url_obj, user):
        """Hard-delete a URL. Raises PermissionError if the user is not the owner."""
        if url_obj.owner != user:
            raise PermissionError("You do not have permission to delete this URL.")
        url_obj.delete()
        return True

    @staticmethod
    def get_click_stats(url_obj, include_recent=False):
        """
        Compute click analytics for a URL.

        """
        clicks_by_country = list(
            Click.objects.filter(url=url_obj)
            .values('country')
            .annotate(total_clicks=Count('id'))
            .order_by('-total_clicks')
        )

        result = {'clicks_by_country': clicks_by_country}

        if include_recent:
            result['recent_clicks'] = list(
                Click.objects.filter(url=url_obj)
                .order_by('-created_at')[:20]
                .values('ip_address', 'country', 'user_agent', 'created_at')
            )

        return result