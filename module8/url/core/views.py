from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection
import logging

# Logger for health checks
logger = logging.getLogger(__name__)

def health_check(request):
    """
    Health check endpoint to verify DB and Redis connectivity.
    Returns 200 if both are OK, 503 if either fails.
    """
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error("Database health check failed", extra={"error": str(e)})

    # Check cache connectivity
    try:
        cache.set("health_check", "ok", timeout=5)
        cache_status = "ok" if cache.get("health_check") == "ok" else "error"
    except Exception as e:
        cache_status = f"error: {str(e)}"
        logger.error("Redis health check failed", extra={"error": str(e)})

    return JsonResponse({
        "database": db_status,
        "cache": cache_status,
    }, status=200 if db_status == "ok" and cache_status == "ok" else 503)