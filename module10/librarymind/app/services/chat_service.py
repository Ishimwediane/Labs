import logging
import uuid
from typing import Any, Dict, List, Optional

from app.config import Settings
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates multi-turn AI librarian conversations with RAG grounding."""

    def __init__(
        self,
        rag_service: RAGService,
        ai_service: ResilientAIService,
        conversation_store: ConversationStore,
        usage_tracker: UsageTracker,
        rate_limiter: TokenBucketRateLimiter,
        settings: Settings,
    ) -> None:
        self.rag_service = rag_service
        self.ai_service = ai_service
        self.conversation_store = conversation_store
        self.usage_tracker = usage_tracker
        self.rate_limiter = rate_limiter
        self.settings = settings
        self.history_limit: int = getattr(settings, "CHAT_HISTORY_LIMIT", 10)
        logger.info(f"ChatService initialised. History limit: {self.history_limit}.")

    def chat(self, conversation_id: Optional[str], message: str) -> Dict[str, Any]:
        """Process one conversation turn and return the assistant's reply.

        Args:
            conversation_id: Unique session identifier. If None or empty,
                             a new UUID is auto-generated and returned.
            message: The patron's current message.

        Returns:
            Dict with keys: reply, sources, conversation_id.
        """
        # Auto-generate a session ID when the client does not provide one.
        if not conversation_id or not conversation_id.strip():
            conversation_id = str(uuid.uuid4())
            logger.info(f"Auto-generated conversation_id: {conversation_id}")

        conversation_id, message = self._validate_inputs(conversation_id, message)
        logger.info(f"[{conversation_id}] New turn: '{message[:60]}...'")

        recent_history = self._truncate_history(
            self.conversation_store.get_history(conversation_id)
        )
        catalogue_context, sources = self._retrieve_context(message)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            history_text=self._format_history(recent_history),
            context_text=catalogue_context,
            message=message,
        )

        self.rate_limiter.acquire()
        reply = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        self.usage_tracker.record_usage(
            provider=self.settings.PRIMARY_PROVIDER,
            model=self._resolve_active_model(),
            prompt=system_prompt + user_prompt,
            completion=reply,
        )

        self.conversation_store.append_message(conversation_id, "user", message)
        self.conversation_store.append_message(conversation_id, "assistant", reply)

        logger.info(f"[{conversation_id}] Reply generated. Sources: {len(sources)}.")
        return {"reply": reply, "sources": sources, "conversation_id": conversation_id}

    def _validate_inputs(self, conversation_id: str, message: str):
        """Strip and validate inputs; raise ValueError only if message is blank."""
        if not message or not message.strip():
            raise ValueError("message must not be empty.")
        return conversation_id.strip(), message.strip()

    def _truncate_history(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return history[-self.history_limit:] if len(history) > self.history_limit else history

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        lines = []
        for msg in history:
            label = "Patron" if msg.get("role") == "user" else "Librarian"
            lines.append(f"{label}: {msg.get('content', '')}")
        return "\n".join(lines)

    def _retrieve_context(self, message: str) -> tuple[str, List[Dict[str, Any]]]:
        try:
            rag_result = self.rag_service.answer_question(message)
        except Exception as exc:
            logger.warning(f"RAG retrieval failed: {exc}. Continuing without context.")
            return "", []

        sources: List[Dict[str, Any]] = rag_result.get("sources", [])
        if not sources:
            return "", []

        context_lines = [
            f"BOOK {i}:\n  Title:  {s.get('title', 'Unknown')}\n"
            f"  Author: {s.get('author', 'Unknown')}\n"
            f"  Relevance score: {s.get('score', 0):.2f}"
            for i, s in enumerate(sources, 1)
        ]
        return "\n\n".join(context_lines), sources

    def _build_system_prompt(self) -> str:
        return (
            "You are a warm, knowledgeable, and friendly AI Librarian for LibraryMind.\n"
            "\n"
            "Your personality:\n"
            "  - Speak conversationally and warmly, like a librarian who genuinely loves books.\n"
            "  - Be concise but never cold.\n"
            "  - Use the patron's own words when possible.\n"
            "\n"
            "Your strict rules:\n"
            "  1. ONLY recommend books that appear in the 'Library Catalogue Context' below.\n"
            "  2. NEVER invent book titles, author names, or plot details.\n"
            "  3. If the catalogue has no relevant books, say so honestly and warmly.\n"
            "  4. Respond naturally to general questions — no forced book recommendations.\n"
            "  5. Always use exact titles and authors from the catalogue.\n"
        )

    def _build_user_prompt(self, history_text: str, context_text: str, message: str) -> str:
        sections: List[str] = []

        if history_text:
            sections.append(
                "Recent Conversation History \n"
                "(Use this to understand follow-up questions.)\n"
                f"{history_text}"
            )

        if context_text:
            sections.append(
                " Library Catalogue Context \n"
                "(These are the ONLY books you may recommend or discuss.)\n"
                f"{context_text}"
            )
        else:
            sections.append(
                "Library Catalogue Context \n"
                "No relevant books were found. Do NOT invent any titles or authors."
            )

        sections.append(f"=== Patron's Current Message ===\n{message}\n\nLibrarian Response:")
        return "\n\n".join(sections)

    def _resolve_active_model(self) -> str:
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        return model_map.get(self.settings.PRIMARY_PROVIDER, self.settings.OPENAI_MODEL)
