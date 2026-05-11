import logging
from typing import List, Dict, Any, Optional

from app.config import Settings
from app.services.embedding_service import EmbeddingService
from app.infrastructure.vector_store import ChromaVectorStore
from app.infrastructure.cache import CacheService
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService

logger = logging.getLogger(__name__)

class RAGService:
    """
    Retrieval-Augmented Generation (RAG) Service.
    Coordinates searching the vector store and generating AI responses.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: ChromaVectorStore,
        cache_service: CacheService,
        rate_limiter: TokenBucketRateLimiter,
        usage_tracker: UsageTracker,
        ai_service: ResilientAIService,
        settings: Settings
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.cache_service = cache_service
        self.rate_limiter = rate_limiter
        self.usage_tracker = usage_tracker
        self.ai_service = ai_service
        self.settings = settings

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Main entry point to answer a patron's question using RAG.
        """
        if not question or len(question.strip()) < 3:
            return {"answer": "Please provide a valid question.", "sources": [], "cached": False}

        # 1. Cache Check
        cache_key = self._make_cache_key(question)
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            logger.info(f"RAG Cache HIT for: {question[:30]}...")
            cached_result["cached"] = True
            return cached_result

        # 2. Rate Limiting (Check before doing expensive AI work)
        self.rate_limiter.acquire()

        # 3. Retrieve Context (Vector Search)
        logger.info(f"Processing new RAG request: {question[:50]}...")
        query_vector = self.embedding_service.generate_query_embedding(question)
        raw_results = self.vector_store.search(
            query_embedding=query_vector, 
            top_k=self.settings.RAG_TOP_K
        )

        # 4. Relevance Filtering
        filtered_results = self._filter_results(raw_results)

        # 5. Handle "No Results" (Anti-Hallucination)
        if not filtered_results:
            logger.info("No relevant books found above threshold. Refusing to answer.")
            return {
                "answer": "I'm sorry, I couldn't find any relevant books in our collection to answer that specific question.",
                "sources": [],
                "cached": False
            }

        # 6. Build Prompts
        context_block = self._build_context(filtered_results)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, context_block)

        # 7. Generate AI Response (Resilient Service)
        # This will automatically fallback if the primary provider is down
        ai_response = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2 # Keep it focused on the facts
        )

        # 8. Usage Tracking (Accounting)
        # We record the tokens and cost for the LLM call
        self.usage_tracker.record_usage(
            provider=self.settings.PRIMARY_PROVIDER,
            model=self.settings.OPENAI_MODEL if self.settings.PRIMARY_PROVIDER == "openai" else self.settings.GEMINI_MODEL,
            prompt=system_prompt + user_prompt,
            completion=ai_response
        )

        # 9. Format Final Response
        final_response = {
            "answer": ai_response,
            "sources": self._build_sources(filtered_results),
            "cached": False
        }

        # 10. Cache Result for future identical questions
        self.cache_service.set(cache_key, final_response)

        return final_response

    def _make_cache_key(self, question: str) -> str:
        """Create a unique fingerprint for the RAG request."""
        return self.cache_service.make_key(
            namespace="rag:v1", 
            payload={"q": question.strip().lower()}
        )

    def _filter_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove books that don't meet the relevance threshold."""
        return [
            r for r in results 
            if r.get("score", 0) >= self.settings.RAG_RELEVANCE_THRESHOLD
        ]

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """Format the retrieved books into a text block for the AI."""
        context_parts = []
        for i, res in enumerate(results, 1):
            part = (
                f"BOOK {i}:\n"
                f"Title: {res.get('title')}\n"
                f"Author: {res.get('author')}\n"
                f"Description: {res.get('description')}\n"
            )
            context_parts.append(part)
        return "\n---\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """The instructions that 'ground' the AI."""
        return (
            "You are a helpful and precise Librarian AI for LibraryMind.\n"
            "Your goal is to answer patron questions ONLY using the provided book context.\n"
            "STRICT RULES:\n"
            "1. If the context does not contain the answer, say you don't know.\n"
            "2. Do not invent books, authors, or facts.\n"
            "3. Always cite the title of the book(s) you are using in your answer.\n"
            "4. Be concise and professional."
        )

    def _build_user_prompt(self, question: str, context: str) -> str:
        """Combine the user's question with the retrieved library data."""
        return (
            f"Context from Library Catalogue:\n{context}\n\n"
            f"Patron Question: {question}\n"
            f"Librarian Answer:"
        )

    def _build_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract clean metadata for the UI to display 'Sources'."""
        return [
            {
                "title": r.get("title"),
                "author": r.get("author"),
                "score": r.get("score")
            }
            for r in results
        ]
