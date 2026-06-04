"""
app/api/dependencies.py
========================
Part 7 — Dependency Injection

WHY THIS FILE EXISTS:
    Every endpoint needs the same set of services (AI, RAG, chat, etc.).
    Building those services on every single request would be wasteful —
    each construction opens connections, loads config, and initialises clients.

    FastAPI's `Depends()` system lets us build each service ONCE at startup
    and reuse the same instance for every request.  This is called the
    "singleton via dependency injection" pattern.

HOW IT WORKS:
    1. Each service is built by a plain Python function (a "provider function").
    2. The function is decorated with @lru_cache so it only runs once.
    3. Route handlers declare the service they need with `Depends(get_xyz)`.
    4. FastAPI calls the provider function, gets the cached instance, and
       injects it into the route handler.

DEPENDENCY GRAPH:
    Settings
        └── ResilientAIService
        └── UsageTracker
        └── TokenBucketRateLimiter
        └── CacheService
        └── EmbeddingService
              └── ChromaVectorStore
                    └── RAGService
                          └── ChatService
                          └── ClassificationService
                          └── SummarisationService
"""

import logging
from functools import lru_cache

from app.config import get_settings, Settings
from app.infrastructure.cache import CacheService
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.infrastructure.vector_store import ChromaVectorStore
from app.providers.resilient_service import ResilientAIService
from app.services.chat_service import ChatService
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService
from app.services.summarisation_service import SummarisationService

logger = logging.getLogger(__name__)


# ======================================================================
# Low-level singletons
# ======================================================================

@lru_cache()
def get_cache_service() -> CacheService:
    """Return a single shared CacheService instance."""
    logger.info("Initialising CacheService...")
    return CacheService()


@lru_cache()
def get_usage_tracker() -> UsageTracker:
    """Return a single shared UsageTracker instance."""
    logger.info("Initialising UsageTracker...")
    return UsageTracker()


@lru_cache()
def get_rate_limiter() -> TokenBucketRateLimiter:
    """Return a single shared TokenBucketRateLimiter instance."""
    logger.info("Initialising RateLimiter...")
    return TokenBucketRateLimiter()


@lru_cache()
def get_ai_service() -> ResilientAIService:
    """Return a single shared ResilientAIService instance."""
    logger.info("Initialising ResilientAIService...")
    return ResilientAIService()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Return a single shared EmbeddingService instance."""
    logger.info("Initialising EmbeddingService...")
    return EmbeddingService()


@lru_cache()
def get_vector_store() -> ChromaVectorStore:
    """Return a single shared ChromaVectorStore instance."""
    logger.info("Initialising ChromaVectorStore...")
    return ChromaVectorStore()


@lru_cache()
def get_conversation_store() -> ConversationStore:
    """Return a single shared ConversationStore instance."""
    logger.info("Initialising ConversationStore...")
    return ConversationStore()


# ======================================================================
# Higher-level service singletons
# ======================================================================

@lru_cache()
def get_rag_service() -> RAGService:
    """Build and return a single shared RAGService instance."""
    logger.info("Initialising RAGService...")
    settings = get_settings()
    return RAGService(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        cache_service=get_cache_service(),
        rate_limiter=get_rate_limiter(),
        usage_tracker=get_usage_tracker(),
        ai_service=get_ai_service(),
        settings=settings,
    )


@lru_cache()
def get_chat_service() -> ChatService:
    """Build and return a single shared ChatService instance."""
    logger.info("Initialising ChatService...")
    settings = get_settings()
    return ChatService(
        rag_service=get_rag_service(),
        ai_service=get_ai_service(),
        conversation_store=get_conversation_store(),
        usage_tracker=get_usage_tracker(),
        rate_limiter=get_rate_limiter(),
        settings=settings,
    )


@lru_cache()
def get_classification_service() -> ClassificationService:
    """Build and return a single shared ClassificationService instance."""
    logger.info("Initialising ClassificationService...")
    settings = get_settings()
    return ClassificationService(
        ai_service=get_ai_service(),
        usage_tracker=get_usage_tracker(),
        rate_limiter=get_rate_limiter(),
        settings=settings,
    )


@lru_cache()
def get_summarisation_service() -> SummarisationService:
    """Build and return a single shared SummarisationService instance."""
    logger.info("Initialising SummarisationService...")
    settings = get_settings()
    return SummarisationService(
        ai_service=get_ai_service(),
        usage_tracker=get_usage_tracker(),
        rate_limiter=get_rate_limiter(),
        settings=settings,
    )
