from celery import shared_task
from django.db.models import F
from django.conf import settings
from .models import Url, Click
from django.utils import timezone
from django.core.cache import cache
import logging
import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_url_metadata_task(self, url_id):
    """
    Async task to fetch page title, description, and favicon via the Preview Service.
    Implements:
    - Retries with exponential backoff
    - Circuit Breaker : Skips domains that fail repeatedly
    """
    try:
        url_obj = Url.objects.get(id=url_id)
        domain = urlparse(url_obj.original_url).netloc
        
        # 1. Circuit Breaker Check
        circuit_breaker_key = f"blocked:{domain}"
        if cache.get(circuit_breaker_key):
            logger.warning(f"Circuit Breaker: Skipping fetch for {domain} (blocked)")
            return {"status": "skipped", "reason": "circuit_breaker"}

        preview_service_url = f"{settings.PREVIEW_SERVICE_URL.rstrip('/')}/fetch-preview/"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(preview_service_url, json={"url": url_obj.original_url})
            response.raise_for_status()
            metadata = response.json()

        # Update the URL model, truncating to prevent Database crashes
        if metadata.get("title"):
            url_obj.title = metadata.get("title")[:255]
        if metadata.get("description"):
            url_obj.description = metadata.get("description")[:500]
            
        url_obj.favicon = metadata.get("favicon")
        url_obj.save(update_fields=["title", "description", "favicon"])

        return metadata

    except Url.DoesNotExist:
        logger.error(f"Url ID {url_id} not found during metadata fetch.")
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        # 2. Track failures for Circuit Breaker
        fail_key = f"fail:{domain}"
        fail_count = cache.get(fail_key, 0) + 1
        cache.set(fail_key, fail_count, timeout=3600)  # Keep fail count for 1 hour

        if fail_count >= 5:
            logger.error(f"Circuit Breaker: Blocking domain {domain} due to {fail_count} failures.")
            cache.set(circuit_breaker_key, True, timeout=600)  # Block for 10 minutes

        logger.warning(
            f"Preview service error for {domain}: {str(e)}. Retry {self.request.retries}/3",
            extra={"url_id": url_id}
        )
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
    except Exception as e:
        logger.error(f"Unexpected error in metadata task: {str(e)}")
        raise


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