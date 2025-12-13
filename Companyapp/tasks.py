from celery import shared_task
from django.utils import timezone
from .models import JobAdvertised
import logging

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_jobs():
    """
    Deletes jobs where the deadline has passed.
    """
    now = timezone.now()
    expired_jobs = JobAdvertised.objects.filter(deadline__lt=now)
    count = expired_jobs.count()
    
    if count > 0:
        expired_jobs.delete()
        logger.info(f"🧹 Auto-deleted {count} expired job(s).")
        return f"Deleted {count} expired jobs."
    
    return "No expired jobs found."