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

    def answer_question(self, question: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point to answer a patron's question using RAG.

        filters (optional dict) can contain:
          - genre    : str  — restrict context to books of this genre
          - year_min : int  — only use books published from this year
          - year_max : int  — only use books published up to this year
        """
        filters = filters or {}
        if not question or len(question.strip()) < 3:
            return {"answer": "Please provide a valid question.", "sources": [], "cached": False}

        # 1. Cache Check (filters are included in the cache key)
        cache_key = self._make_cache_key(question, filters)
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            logger.info(f"RAG Cache HIT for: {question[:30]}...")
            cached_result["cached"] = True
            return cached_result

        # 2. Rate Limiting (Check before doing expensive AI work)
        self.rate_limiter.acquire()

        # 3. Retrieve Context (Vector Search)
        # If filters are active we fetch the whole catalogue so nothing is missed.
        # Without filters, just fetch RAG_TOP_K (efficient).
        has_filters = any(v for v in filters.values() if v is not None)
        fetch_k = 100 if has_filters else self.settings.RAG_TOP_K

        logger.info(f"Processing new RAG request: {question[:50]}...")
        query_vector = self.embedding_service.embed_text(question)
        raw_results = self.vector_store.search(
            query_embedding=query_vector,
            top_k=fetch_k
        )

        # 4. Apply metadata filters (genre, year range)
        raw_results = self._apply_filters(raw_results, filters)
        filtered_results = self._filter_results(raw_results)

        # 5. Handle "No Results" (Anti-Hallucination)
        if not filtered_results:
            logger.info("No relevant books found above threshold. Returning helpful no-results message.")
            return {
                "answer": (
                    "I searched through the LibraryMind catalogue but couldn't find any books "
                    "that closely match your question.\n\n"
                    "Here are a few tips to find what you're looking for:\n"
                    "  • Try broader keywords (e.g. 'mystery' instead of 'murder in Paris')\n"
                    "  • Search by author name if you have one in mind\n"
                    "  • Filter by genre using the genre field in your request\n"
                    "  • Try a related topic or synonyms\n\n"
                    "This search only covers books in LibraryMind's catalogue. "
                    "If you're looking for general book recommendations or author information, "
                    "feel free to ask the chat assistant instead!"
                ),
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
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        self.usage_tracker.record_usage(
            provider=self.settings.PRIMARY_PROVIDER,
            model=model_map.get(self.settings.PRIMARY_PROVIDER, self.settings.OPENAI_MODEL),
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

    def _make_cache_key(self, question: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Create a unique fingerprint for the RAG request including any active filters."""
        payload: Dict[str, Any] = {"q": question.strip().lower()}
        if filters:
            # Only include non-None filter values so cache keys stay compact
            active = {k: v for k, v in filters.items() if v is not None}
            if active:
                payload["filters"] = active
        return self.cache_service.make_key(namespace="rag:v1", payload=payload)

    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter retrieved books by genre and year before passing to the LLM."""
        filtered = results

        genre = filters.get("genre")
        if genre:
            # Exact match, case-insensitive
            filtered = [r for r in filtered if r.get("genre", "").lower() == genre.lower()]

        year_min = filters.get("year_min")
        if year_min is not None:
            filtered = [r for r in filtered if r.get("year", 0) >= year_min]

        year_max = filters.get("year_max")
        if year_max is not None:
            filtered = [r for r in filtered if r.get("year", 9999) <= year_max]

        return filtered

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
        """The instructions that ground the AI to the library catalogue."""
        return (
            "You are a knowledgeable and friendly Librarian AI for LibraryMind — a book search assistant.\n"
            "\n"
            "YOUR PURPOSE:\n"
            "  Answer questions about books that exist in the LibraryMind catalogue.\n"
            "  The catalogue context provided below is your ONLY source of truth.\n"
            "\n"
            "RULES (strictly follow these):\n"
            "  1. ONLY discuss books that appear in the 'Library Catalogue' section below.\n"
            "  2. NEVER invent book titles, authors, ISBNs, publication years, or plot summaries.\n"
            "  3. ALWAYS cite the exact title and author for every book you mention.\n"
            "  4. If the question is answered by one book, be concise and clear.\n"
            "  5. If multiple books are relevant, compare them briefly to help the patron decide.\n"
            "  6. If the question is not about books at all (e.g. weather, coding, sports),\n"
            "     politely explain that this is a book search tool and redirect them.\n"
            "  7. Be warm and encouraging — reading is something worth being excited about!\n"
        )

    def _build_user_prompt(self, question: str, context: str) -> str:
        """Combine the patron's question with the retrieved catalogue entries."""
        return (
            "=== Library Catalogue (search results for this question) ===\n"
            f"{context}\n"
            "\n"
            "LIMITATION: You may only refer to the books listed above. "
            "Do not mention any book not in this catalogue.\n"
            "\n"
            f"=== Patron's Question ===\n{question}\n"
            "\n"
            "=== Your Answer (cite exact titles & authors from the catalogue) ==="
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
