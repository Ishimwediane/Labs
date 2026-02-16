from celery import shared_task
from .models import Url, Click
from django.utils import timezone
import logging

# Logger for Celery tasks
logger = logging.getLogger(__name__)

@shared_task
def track_click_task(url_id,ip_address,user_agent):
    """
    Async task to track URL clicks without blocking the redirect.
    This is the "write-behind" pattern for better performance.
    """
    try:
        url=Url.objects.get(id=url_id)
        
        Click.objects.create(url=url,ip_address=ip_address,user_agent=user_agent)
        url.click_count+=1
        url.save(update_fields=['click_count'])
        
        # Log successful click tracking
        logger.info(
            "Click tracked successfully",
            extra={
                "url_id": url_id,
                "short_code": url.short_url,
                "ip": ip_address
            }
        )
    except Url.DoesNotExist:
        # Log error if URL not found
        logger.error(
            "Click tracking failed - URL not found",
            extra={"url_id": url_id}
        )
    except Exception as e:
        # Log any other errors
        logger.error(
            "Click tracking failed",
            extra={
                "url_id": url_id,
                "error": str(e)
            }
        )

@shared_task
def cleanup_expired_urls():
    """
    Periodic task to deactivate expired URLs.
    Runs nightly via Celery Beat.
    """
    try:
        expired_urls=Url.objects.filter(expiry_date__lt=timezone.now())
        count=expired_urls.update(is_active=False)
        
        # Log cleanup results
        logger.info(
            "Expired URLs cleanup completed",
            extra={"deactivated_count": count}
        )
        
        return f"Deactivated {count} expired URLs"
    except Exception as e:
        # Log cleanup errors
        logger.error(
            "Expired URLs cleanup failed",
            extra={"error": str(e)}
        )
        raise