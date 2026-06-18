"""
Endpoints:
    POST /search/books  — semantic vector search over the catalogue
    POST /search/ask    — RAG-powered Q&A (question → grounded answer)
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_embedding_service,
    get_vector_store,
    get_rag_service,
)
from app.api.models import (
    AskRequest,
    AskResponse,
    BookResult,
    BookSearchRequest,
    BookSearchResponse,
)
from app.infrastructure.rate_limiter import RateLimitExceededError
from app.services.embedding_service import EmbeddingService
from app.infrastructure.vector_store import ChromaVectorStore
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


# POST /search/books
@router.post(
    "/books",
    response_model=BookSearchResponse,
    summary="Semantic book search",
    description=(
        "Embed the query and search the ChromaDB catalogue for the most "
        "semantically similar books. Returns books ranked by cosine similarity."
    ),
    responses={
        429: {"description": "Rate limit exceeded."},
        503: {"description": "All AI embedding providers failed."},
    },
)
async def search_books(
    body: BookSearchRequest,
    embedding_svc: Annotated[EmbeddingService, Depends(get_embedding_service)],
    vector_store:  Annotated[ChromaVectorStore,  Depends(get_vector_store)],
) -> BookSearchResponse:
    """
    Embed the query string and run a vector similarity search over the
    library catalogue stored in ChromaDB.
    """
    try:
        query_vector = embedding_svc.embed_text(body.query)
    except Exception as exc:
        logger.error(f"Embedding failed for search query: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {exc}",
        )

    raw_results = vector_store.search(query_embedding=query_vector, top_k=body.limit)

    books = [BookResult(**r) for r in raw_results]

    return BookSearchResponse(
        results=books,
        total=len(books),
        query=body.query,
    )



# POST /search/ask

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="RAG-powered Q&A",
    description=(
        "Answer a natural-language question using Retrieval-Augmented Generation. "
        "The answer is grounded exclusively in the library catalogue — the model "
        "will not invent books or authors."
    ),
    responses={
        429: {"description": "Rate limit exceeded."},
        503: {"description": "All AI providers failed."},
    },
)
async def ask_question(
    body: AskRequest,
    rag_svc: Annotated[RAGService, Depends(get_rag_service)],
) -> AskResponse:
    """
    Run a full RAG pipeline: embed the question → retrieve relevant books →
    generate a grounded answer → return answer + sources + cache flag.
    """
    try:
        result = rag_svc.answer_question(body.question)
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before sending another request.",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI provider unavailable: {exc}",
        )
    except Exception as exc:
        logger.error(f"Unexpected error in /search/ask: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unexpected error: {exc}",
        )

    return AskResponse(
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
        cached=result.get("cached", False),
    )
