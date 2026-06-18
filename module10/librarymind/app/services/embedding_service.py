import logging
from typing import List, Optional

from google import genai
from app.config import get_settings
from app.infrastructure.cache import CacheService
from app.infrastructure.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using Gemini.
    Includes caching to avoid redundant API calls.

    Why Gemini?
    - OpenAI embeddings require paid credits.
    - Gemini embedding API has a free tier generous enough for development.
    - IMPORTANT: Whatever model seeds the books into ChromaDB MUST be the
      same model used at search time. Both use Gemini here.
    """

    def __init__(self, usage_tracker: Optional[UsageTracker] = None):
        self.settings = get_settings()
        self.cache = CacheService()
        self.usage_tracker = usage_tracker

        # Gemini is our single embedding provider.
        # Model: gemini-embedding-001 → produces 3072-dimension vectors.
        self.gemini_client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        self.gemini_model = self.settings.GEMINI_EMBEDDING_MODEL

        logger.info(f"Embedding Service initialized. Model: {self.gemini_model}")

    def _make_embedding_cache_key(self, text: str, model: str) -> str:
        """Create a cache key for a specific text embedding."""
        return self.cache.make_key("embedding", {"text": text, "model": model})

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single string using Gemini.

        What this does (simply):
        - Takes your text (e.g. "books about space")
        - Sends it to Gemini's embedding API
        - Gets back a list of 3072 numbers representing the meaning
        - Saves it in Redis cache so the next identical query is FREE
        """
        if not text:
            return []

        # Step 1: Check Redis cache first — if this exact text was already
        # embedded before, return it instantly without calling Gemini.
        cache_key = self._make_embedding_cache_key(text, self.gemini_model)
        cached_embedding = self.cache.get(cache_key)
        if cached_embedding:
            logger.debug("Embedding cache HIT — no API call needed.")
            return cached_embedding

        # Step 2: Cache miss — call Gemini API to generate the embedding.
        try:
            logger.info(f"Calling Gemini embedding API for: {text[:50]}...")
            result = self.gemini_client.models.embed_content(
                model=self.gemini_model,
                contents=text
            )

            # Extract the vector from Gemini's response format
            if hasattr(result, 'embeddings') and result.embeddings:
                embedding = list(result.embeddings[0].values)
            else:
                embedding = list(result.embeddings.values)

            # Step 3: Save to cache for future identical queries.
            self.cache.set(cache_key, embedding)

            # Step 4: Record usage (cost tracking).
            if self.usage_tracker:
                self.usage_tracker.record_usage(
                    provider="gemini",
                    model=self.gemini_model,
                    prompt=text,
                    completion=""  # No output tokens for embeddings
                )

            return embedding

        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            raise RuntimeError(f"Embedding service unavailable: {e}") from e

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of strings.
        Used by seed_books.py to embed all 20 books at startup.
        """
        return [self.embed_text(t) for t in texts]
