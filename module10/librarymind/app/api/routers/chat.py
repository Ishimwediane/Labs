"""
Endpoints:
    POST /chat                             — multi-turn AI librarian conversation
    GET  /chat/sessions                    — list active sessions (paginated + filtered)
    GET  /chat/sessions/{conversation_id}  — full history for one session
"""

import logging
import math
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_chat_service, get_conversation_store
from app.api.models import (
    ChatRequest,
    ChatResponse,
    SessionHistoryResponse,
    SessionListResponse,
    SessionSummary,
)
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import RateLimitExceededError
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# ── POST /chat ──────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ChatResponse,
    summary="Multi-turn AI librarian chat",
    description=(
        "Send a message to the AI librarian. "
        "**`conversation_id` is optional** — if you omit it, the server creates a "
        "new session and returns the generated ID. "
        "Pass that same ID on every subsequent turn to keep conversation memory. "
        "Each reply is grounded in the library catalogue via RAG."
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
    - Auto-generates a conversation_id if one is not supplied
    - Loads history for the given conversation_id
    - Retrieves relevant books from ChromaDB (RAG)
    - Generates a context-aware reply
    - Saves both the user message and assistant reply to memory (Redis or in-memory)
    """
    try:
        result = chat_svc.chat(
            conversation_id=body.conversation_id,   # may be None — service handles it
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


# ── GET /chat/sessions ──────────────────────────────────────────────────


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="List active chat sessions",
    description=(
        "Returns a paginated, optionally filtered list of all active conversation sessions. "
        "Use `min_messages` to filter out very short sessions. "
        "Use `last_role` to show only sessions where the last speaker was 'user' or 'assistant'."
    ),
)
async def list_sessions(
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
    page: int = Query(default=1, ge=1, description="Page number (starts at 1)."),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page (1–100)."),
    min_messages: Optional[int] = Query(
        default=None, ge=1,
        description="Only include sessions with at least this many messages.",
    ),
    last_role: Optional[str] = Query(
        default=None,
        description="Filter by the role of the last message: 'user' or 'assistant'.",
    ),
) -> SessionListResponse:
    """
    List all active sessions with lightweight metadata.

    Works regardless of whether Redis or the in-memory fallback is active.
    """
    if last_role is not None and last_role not in ("user", "assistant"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="last_role must be 'user' or 'assistant'.",
        )

    all_ids = store.list_conversations()

    # Build summaries and apply filters
    summaries: list[SessionSummary] = []
    for conv_id in all_ids:
        history = store.get_history(conv_id)
        count = len(history)

        if min_messages is not None and count < min_messages:
            continue

        last_msg = history[-1] if history else None
        role = last_msg.get("role") if last_msg else None

        if last_role is not None and role != last_role:
            continue

        summaries.append(
            SessionSummary(
                conversation_id=conv_id,
                message_count=count,
                last_role=role,
                last_message_preview=(
                    (last_msg.get("content", "")[:80]) if last_msg else None
                ),
                last_active=(last_msg.get("timestamp") if last_msg else None),
            )
        )

    # Sort by last_active descending (most recently active first)
    summaries.sort(key=lambda s: s.last_active or "", reverse=True)

    total = len(summaries)
    total_pages = max(1, math.ceil(total / limit))
    start = (page - 1) * limit
    end = start + limit
    page_items = summaries[start:end]

    return SessionListResponse(
        sessions=page_items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        storage_backend=store.backend,
    )


# ── GET /chat/sessions/{conversation_id} ───────────────────────────────


@router.get(
    "/sessions/{conversation_id}",
    response_model=SessionHistoryResponse,
    summary="Get full history for a session",
    description=(
        "Returns the complete ordered message history (oldest first) for the given "
        "`conversation_id`. Returns **404** if the session does not exist or has expired."
    ),
    responses={
        404: {"description": "Session not found."},
    },
)
async def get_session_history(
    conversation_id: str,
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> SessionHistoryResponse:
    """Return the full message history for a single conversation."""
    if not store.session_exists(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{conversation_id}' not found or has expired.",
        )

    messages = store.get_history(conversation_id)

    return SessionHistoryResponse(
        conversation_id=conversation_id,
        messages=messages,
        message_count=len(messages),
        storage_backend=store.backend,
    )
