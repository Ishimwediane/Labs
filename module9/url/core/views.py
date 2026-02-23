from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.core.cache import cache
from django.db import connection
import logging

# Logger for health checks
logger = logging.getLogger(__name__)

@extend_schema(
    responses={
        200: {
            "type": "object",
            "properties": {
                "database": {"type": "string", "example": "ok"},
                "cache": {"type": "string", "example": "ok"},
            },
        },
        503: {
            "type": "object",
            "properties": {
                "database": {"type": "string", "example": "error: ..."},
                "cache": {"type": "string", "example": "ok"},
            },
        },
    },
    summary="Health Check",
    description="Verifies DB and Redis connectivity. Returns 200 if both OK, 503 if either fails.",
    tags=["Health"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify DB and Redis connectivity.
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

    http_status = 200 if db_status == "ok" and cache_status == "ok" else 503
    return Response({
        "database": db_status,
        "cache": cache_status,
    }, status=http_status)