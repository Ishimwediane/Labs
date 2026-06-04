"""
app/api/routers/summarise.py
=============================
Part 7 — Review Summarisation Endpoint

Endpoint:
    POST /summarise/reviews — summarise 1–50 reviews into structured JSON
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_summarisation_service
from app.api.models import ReviewSummarisationRequest, ReviewSummarisationResponse
from app.infrastructure.rate_limiter import RateLimitExceededError
from app.services.summarisation_service import SummarisationService, MAX_REVIEWS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summarise", tags=["Summarisation"])


@router.post(
    "/reviews",
    response_model=ReviewSummarisationResponse,
    summary="Summarise book reviews",
    description=(
        f"Analyse a list of 1–{MAX_REVIEWS} book reviews holistically and return "
        "a structured summary containing overall sentiment, estimated average rating, "
        "key themes, praise, criticism, and a recommendation."
    ),
    responses={
        429: {"description": "Rate limit exceeded."},
        503: {"description": "All AI providers failed or returned invalid JSON."},
    },
)
async def summarise_reviews(
    body: ReviewSummarisationRequest,
    summariser: Annotated[SummarisationService, Depends(get_summarisation_service)],
) -> ReviewSummarisationResponse:
    """
    Run the full summarisation pipeline:
    - Validate the review list (1–50 non-empty strings)
    - Build a holistic analysis prompt
    - Send through ResilientAIService (OpenAI → Claude → Gemini)
    - Strip markdown fences, parse JSON, validate field types
    - Return the structured summary
    """
    try:
        result = summariser.summarise_reviews(body.reviews)
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before submitting more reviews.",
        )
    except ValueError as exc:
        # Input validation failure (too many reviews, bad types, etc.)
        # or JSON parsing/validation failure from the model
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Summarisation failed — model returned invalid output: {exc}",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI provider unavailable: {exc}",
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /summarise/reviews: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unexpected error: {exc}",
        )

    return ReviewSummarisationResponse(**result)
