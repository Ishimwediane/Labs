import logging
from app.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.infrastructure.vector_store import ChromaVectorStore
from app.infrastructure.cache import CacheService
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_rag_engine():
    settings = get_settings()
    
    # Instantiate all dependencies
    logger.info("Initializing RAG Engine dependencies...")
    embedding_svc = EmbeddingService()
    vector_store = ChromaVectorStore()
    cache_svc = CacheService()
    rate_limiter = TokenBucketRateLimiter()
    usage_tracker = UsageTracker()
    ai_service = ResilientAIService()
    
    # Instantiate the RAG Service
    rag_service = RAGService(
        embedding_service=embedding_svc,
        vector_store=vector_store,
        cache_service=cache_svc,
        rate_limiter=rate_limiter,
        usage_tracker=usage_tracker,
        ai_service=ai_service,
        settings=settings
    )
    
    # Test Question
    question = "I want a science fiction book about survival on a desert planet."
    
    print(f"\n--- Paton Question: '{question}' ---")
    
    # First Call (Expect a real AI call)
    logger.info("Processing first call (expecting AI generation)...")
    result1 = rag_service.answer_question(question)
    
    print(f"\n[RESPONSE 1]")
    print(f"Answer: {result1['answer']}")
    print(f"Sources: {[s['title'] for s in result1['sources']]}")
    print(f"Cached: {result1['cached']}")
    
    # Second Call (Expect a Cache HIT)
    logger.info("\nProcessing second call (expecting Cache HIT)...")
    result2 = rag_service.answer_question(question)
    
    print(f"\n[RESPONSE 2]")
    print(f"Answer: {result2['answer']}")
    print(f"Sources: {[s['title'] for s in result2['sources']]}")
    print(f"Cached: {result2['cached']}")
    
    # Print usage stats
    print(f"\n--- Total Session Cost: ${usage_tracker.get_daily_cost():.6f} ---")

if __name__ == "__main__":
    try:
        test_rag_engine()
    except Exception as e:
        logger.error(f"Test failed: {e}")
