
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



# Low-level singletons


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
    """Return a single shared EmbeddingService instance, wired with UsageTracker."""
    logger.info("Initialising EmbeddingService...")
    return EmbeddingService(usage_tracker=get_usage_tracker())


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



# Higher-level service singletons


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
