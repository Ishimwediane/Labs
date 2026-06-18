"""

Endpoint:
    POST /chat — multi-turn AI librarian conversation
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_chat_service
from app.api.models import ChatRequest, ChatResponse
from app.infrastructure.rate_limiter import RateLimitExceededError
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Multi-turn AI librarian chat",
    description=(
        "Send a message to the AI librarian. Pass the same `conversation_id` "
        "on every turn to maintain conversation memory. Each reply is grounded "
        "in the library catalogue via RAG."
    ),
    responses={
        429: {"description": "Rate limit exceeded."},
        503: {"description": "All AI providers failed."},
    },
)
async def chat(
    body: ChatRequest,
    chat_svc: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    """
    Process one turn of a multi-turn chat session.

    The service:
    - Loads history for the given conversation_id
    - Retrieves relevant books from ChromaDB (RAG)
    - Generates a context-aware reply
    - Saves both the user message and assistant reply to memory
    """
    try:
        result = chat_svc.chat(
            conversation_id=body.conversation_id,
            message=body.message,
        )
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before sending another message.",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI provider unavailable: {exc}",
        )
    except ValueError as exc:
        # e.g. empty conversation_id or message (double-checked after Pydantic)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /chat: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unexpected error: {exc}",
        )

    return ChatResponse(
        reply=result["reply"],
        sources=result.get("sources", []),
        conversation_id=result["conversation_id"],
    )
