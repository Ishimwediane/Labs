from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.core.cache import cache
from django.db import connection

def health_check(request):
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check cache connectivity
    try:
        cache.set("health_check", "ok", timeout=5)
        cache_status = "ok" if cache.get("health_check") == "ok" else "error"
    except Exception as e:
        cache_status = f"error: {str(e)}"

    return JsonResponse({
        "database": db_status,
        "cache": cache_status,
    }, status=200 if db_status == "ok" and cache_status == "ok" else 503)