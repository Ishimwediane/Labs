"""
Endpoint:
    POST /classify/ticket — classify a support ticket into structured JSON
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_classification_service
from app.api.models import TicketRequest, TicketClassificationResponse
from app.infrastructure.rate_limiter import RateLimitExceededError
from app.services.classification_service import ClassificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post(
    "/ticket",
    response_model=TicketClassificationResponse,
    summary="Classify a support ticket",
    description=(
        "Analyse a raw support ticket and return a structured classification "
        "containing category, priority, sentiment, department, and a summary. "
        "The model is instructed to return JSON only — no free-form text."
    ),
    responses={
        429: {"description": "Rate limit exceeded."},
        503: {"description": "All AI providers failed or returned invalid JSON."},
    },
)
async def classify_ticket(
    body: TicketRequest,
    classifier: Annotated[ClassificationService, Depends(get_classification_service)],
) -> TicketClassificationResponse:
    """
    Run the full classification pipeline:
    - Build a strict JSON-only prompt
    - Send through ResilientAIService (OpenAI → Claude → Gemini)
    - Strip markdown fences, parse JSON, validate required fields and enum values
    - Return the structured classification
    """
    try:
        result = classifier.classify_ticket(body.ticket_text)
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before classifying another ticket.",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Classification failed — model returned invalid output: {exc}",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI provider unavailable: {exc}",
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /classify/ticket: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unexpected error: {exc}",
        )

    return TicketClassificationResponse(**result)
