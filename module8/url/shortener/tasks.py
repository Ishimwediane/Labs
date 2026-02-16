from celery import shared_task
from .models import URL,Click

@shared_task
def track_click_task(url_id,ip_address,user_agent):
    url=URL.objects.get(id=url_id)
    
    Click.objects.create(url=url,ip_address=ip_address,user_agent=user_agent)
    url.click_count+=1
    url.save(update_fields=['click_count'])

@shared_task
def cleanup_expired_urls():
    expired_urls=URL.objects.filter(expiry_date__lt=timezone.now())
    count=expired_urls.update(is_active=False)
    return f"Deactivated {count} expired URLs"