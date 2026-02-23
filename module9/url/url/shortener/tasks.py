from celery import shared_task
from django.db.models import F
from .models import Url, Click
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def track_click_task(url_id, ip_address, user_agent, referer=""):
    """
    Async task to track URL clicks without blocking the redirect.
    This is the "write-behind" pattern for better performance.
    """
    try:
        Click.objects.create(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer or None,
            country="Unknown",   # Real geo-IP lookup would go here
        )
        
        Url.objects.filter(id=url_id).update(click_count=F('click_count') + 1)

        logger.info(
            "Click tracked successfully",
            extra={"url_id": url_id, "ip": ip_address}
        )
    except Exception as e:
        logger.error(
            "Click tracking failed",
            extra={"url_id": url_id, "error": str(e)}
        )
        raise


@shared_task
def cleanup_expired_urls():
    """
    Periodic task to deactivate expired URLs.
    Runs nightly via Celery Beat.
    """
    try:
        expired_urls = Url.objects.filter(expires_at__lt=timezone.now(), is_active=True)
        count = expired_urls.update(is_active=False)

        logger.info(
            "Expired URLs cleanup completed",
            extra={"deactivated_count": count}
        )
        return f"Deactivated {count} expired URLs"
    except Exception as e:
        logger.error(
            "Expired URLs cleanup failed",
            extra={"error": str(e)}
        )
        raise