import logging
from typing import List, Optional

from openai import OpenAI
from google import genai
from app.config import get_settings
from app.infrastructure.cache import CacheService

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings.
    Tries OpenAI first (as per preference), falls back to Gemini if OpenAI is unavailable.
    Includes caching to avoid redundant API calls.
    """

    def __init__(self):
        self.settings = get_settings()
        self.cache = CacheService()
        
        # Initialize OpenAI
        self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.openai_model = self.settings.OPENAI_EMBEDDING_MODEL
        
        # Initialize Gemini
        self.gemini_client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
        self.gemini_model = self.settings.GEMINI_EMBEDDING_MODEL
        
        logger.info(f"Embedding Service initialized. Primary: {self.openai_model}, Fallback: {self.gemini_model}")

    def _make_embedding_cache_key(self, text: str, model: str) -> str:
        """Create a cache key for a specific text embedding."""
        return self.cache.make_key("embedding", {"text": text, "model": model})

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single string.
        Tries OpenAI first, then Gemini.
        """
        if not text:
            return []

        # 1. Try OpenAI
        try:
            cache_key = self._make_embedding_cache_key(text, self.openai_model)
            cached_embedding = self.cache.get(cache_key)
            if cached_embedding:
                logger.debug(f"OpenAI embedding cache HIT.")
                return cached_embedding

            logger.info(f"Attempting OpenAI embedding for: {text[:30]}...")
            response = self.openai_client.embeddings.create(
                input=[text],
                model=self.openai_model
            )
            embedding = response.data[0].embedding
            self.cache.set(cache_key, embedding)
            return embedding

        except Exception as e:
            logger.warning(f"OpenAI embedding failed, falling back to Gemini. Error: {e}")
            
            # 2. Fallback to Gemini
            try:
                cache_key = self._make_embedding_cache_key(text, self.gemini_model)
                cached_embedding = self.cache.get(cache_key)
                if cached_embedding:
                    logger.debug(f"Gemini embedding cache HIT.")
                    return cached_embedding

                logger.info(f"Attempting Gemini embedding for: {text[:30]}...")
                result = self.gemini_client.models.embed_content(
                    model=self.gemini_model,
                    contents=text
                )
                
                # Handling different return formats if necessary
                if hasattr(result, 'embeddings') and result.embeddings:
                    embedding = result.embeddings[0].values
                else:
                    # Depending on SDK version, it might be different
                    embedding = result.embeddings.values if hasattr(result.embeddings, 'values') else result.embeddings

                self.cache.set(cache_key, list(embedding))
                return list(embedding)
            except Exception as ge:
                logger.error(f"Gemini embedding also failed: {ge}")
                raise ge

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of strings.
        """
        return [self.embed_text(t) for t in texts]
