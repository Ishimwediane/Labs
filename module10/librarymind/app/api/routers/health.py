"""
app/api/routers/health.py
==========================
Part 7 — Health Check Endpoint

Endpoint:
    GET /health — returns application status, total AI requests, and daily spend
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_usage_tracker
from app.api.models import HealthResponse
from app.config import get_settings
from app.infrastructure.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Returns the current application status. "
        "Includes total AI requests made since server start and "
        "estimated AI spend for today in USD. "
        "Useful for monitoring dashboards and smoke tests."
    ),
)
async def health_check(
    tracker: Annotated[UsageTracker, Depends(get_usage_tracker)],
) -> HealthResponse:
    """
    Simple health check that also surfaces usage metrics.
    Always returns HTTP 200 when the server is reachable.
    """
    settings = get_settings()

    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        primary_provider=settings.PRIMARY_PROVIDER,
        total_requests=tracker.get_total_requests(),
        daily_cost_usd=round(tracker.get_daily_cost(), 6),
    )
