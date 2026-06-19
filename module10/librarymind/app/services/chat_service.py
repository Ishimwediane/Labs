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


class SessionCapExceededError(Exception):
    """Raised when a session has reached its maximum message count."""


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
        self.max_messages: int = getattr(settings, "MAX_MESSAGES_PER_SESSION", 20)
        logger.info(
            f"ChatService initialised. History limit: {self.history_limit}. "
            f"Session cap: {self.max_messages} messages."
        )

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

        # Enforce session message cap BEFORE any expensive AI calls.
        current_count = self.conversation_store.get_message_count(conversation_id)
        if current_count >= self.max_messages:
            logger.warning(
                f"[{conversation_id}] Session cap reached: "
                f"{current_count}/{self.max_messages} messages."
            )
            raise SessionCapExceededError(
                f"This session has reached the maximum of {self.max_messages} messages "
                f"({self.max_messages // 2} turns). "
                "Please start a new session or reset this one via "
                f"POST /chat/sessions/{conversation_id}/reset."
            )
        recent_history = self._truncate_history(
            self.conversation_store.get_history(conversation_id)
        )

        # Route: classify intent first.
        # - catalogue_lookup  → always try RAG
        # - book_knowledge    → try RAG too; use catalogue if found, else fall back to AI knowledge
        # - general (off-topic) → skip RAG entirely
        intent = self._classify_intent(message)
        logger.info(f"[{conversation_id}] Intent classified as: '{intent}'")

        if intent in {"catalogue_lookup", "book_knowledge"}:
            catalogue_context, sources = self._retrieve_context(message)
            # If the catalogue returned results for a book_knowledge question,
            # upgrade the effective intent so the AI is grounded in those books.
            if sources and intent == "book_knowledge":
                intent = "catalogue_lookup"
                logger.info(f"[{conversation_id}] Upgraded intent to 'catalogue_lookup' — catalogue has matching books.")
        else:
            # Completely off-topic — skip RAG entirely.
            catalogue_context, sources = "", []

        has_context = bool(catalogue_context)

        system_prompt = self._build_system_prompt(intent=intent, has_context=has_context)
        user_prompt = self._build_user_prompt(
            history_text=self._format_history(recent_history),
            context_text=catalogue_context,
            message=message,
            intent=intent,
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

    def _classify_intent(self, message: str) -> str:
        """Classify the patron's message into one of three routing intents.

        Returns:
            'catalogue_lookup'  — question needs the library's book catalogue (use RAG).
            'book_knowledge'    — general book/author question answerable from AI knowledge.
            'general'           — off-topic question unrelated to books.
        """
        system = (
            "You are an intent classifier for a library AI assistant.\n"
            "Classify the patron's message into EXACTLY ONE of these labels:\n"
            "  catalogue_lookup  — asks about books/authors available in THIS library's catalogue\n"
            "  book_knowledge    — asks about books, authors, or reading in general (not catalogue-specific)\n"
            "  general           — unrelated to books or libraries\n"
            "Reply with only the label. No punctuation. No explanation."
        )
        user = f"Message: {message}\nLabel:"
        try:
            raw = self.ai_service.generate(
                prompt=user,
                system=system,
                temperature=0.0,
                max_tokens=10,
            )
            label = raw.strip().lower().split()[0] if raw.strip() else "general"
            if label not in {"catalogue_lookup", "book_knowledge", "general"}:
                label = "general"
            return label
        except Exception as exc:
            logger.warning(f"Intent classification failed: {exc}. Defaulting to catalogue_lookup.")
            return "catalogue_lookup"  # safe fallback — still tries RAG

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

    def _build_system_prompt(self, intent: str = "catalogue_lookup", has_context: bool = True) -> str:
        base = (
            "You are a warm, knowledgeable, and friendly AI Librarian named 'Mira' for LibraryMind.\n"
            "LibraryMind is a digital library assistant — your specialty is BOOKS.\n"
            "\n"
            "Your personality:\n"
            "  - Speak warmly and conversationally, like a librarian who genuinely loves books.\n"
            "  - Always be helpful, concise, and never cold or robotic.\n"
            "  - Use encouraging language — reading is a joy you want to share.\n"
            "\n"
            "Your scope (IMPORTANT):\n"
            "  - You are a BOOK specialist. Your primary purpose is helping patrons find,\n"
            "    learn about, and enjoy books and reading.\n"
            "  - You may discuss books, authors, genres, reading tips, and literary topics.\n"
            "  - For questions completely unrelated to books or reading, politely redirect\n"
            "    the patron back to your book-focused purpose.\n"
            "\n"
        )

        if intent == "catalogue_lookup" and has_context:
            base += (
                "CATALOGUE SEARCH MODE — Books were found in this library's collection:\n"
                "  1. ONLY recommend or discuss books listed in the 'Library Catalogue Context'.\n"
                "  2. NEVER invent titles, author names, ISBNs, or plot details.\n"
                "  3. Always cite the exact title and author from the catalogue.\n"
                "  4. Highlight what makes each book relevant to the patron's question.\n"
                "  5. If multiple books match, briefly compare them to help the patron choose.\n"
            )
        elif intent == "catalogue_lookup" and not has_context:
            base += (
                "CATALOGUE SEARCH MODE — No matching books were found:\n"
                "  1. Apologise warmly and honestly that the library does not have a match.\n"
                "  2. Suggest the patron try different keywords or genres.\n"
                "  3. You MAY briefly mention 1-2 well-known books on the topic from your general\n"
                "     knowledge, but clearly state they are NOT in this library's catalogue.\n"
                "  4. Invite the patron to ask about something else in the collection.\n"
            )
        elif intent == "book_knowledge":
            base += (
                "BOOK KNOWLEDGE MODE — Answering from general literary knowledge:\n"
                "  1. Answer confidently using your knowledge of books, authors, and literature.\n"
                "  2. Be accurate — do not invent facts about real books or authors.\n"
                "  3. If relevant, mention that LibraryMind may have related books available\n"
                "     and invite the patron to ask for a catalogue search.\n"
                "  4. Keep answers focused on reading and books.\n"
            )
        else:  # general / off-topic
            base += (
                "OUT-OF-SCOPE MESSAGE — The question is not related to books or reading:\n"
                "  1. Politely and warmly acknowledge the question.\n"
                "  2. Explain that as a library assistant, you specialise in books and reading.\n"
                "  3. Redirect by asking what book topics or titles you can help them with.\n"
                "  4. Keep it brief, friendly, and never dismissive.\n"
                "  Example tone: 'That's a bit outside my bookshelf! I'm best at helping\n"
                "  you find great reads. Is there a book or topic I can search for you?'\n"
            )
        return base

    def _build_user_prompt(
        self, history_text: str, context_text: str, message: str, intent: str = "catalogue_lookup"
    ) -> str:
        sections: List[str] = []

        if history_text:
            sections.append(
                "=== Conversation History ===\n"
                "(Refer to this for follow-up questions and context.)\n"
                f"{history_text}"
            )

        if intent == "catalogue_lookup":
            if context_text:
                sections.append(
                    "=== Library Catalogue Results ===\n"
                    "The following books were found in LibraryMind's collection.\n"
                    "Discuss ONLY these books — do not invent or add others.\n"
                    f"{context_text}"
                )
            else:
                sections.append(
                    "=== Library Catalogue Results ===\n"
                    "No books matched this search in LibraryMind's collection.\n"
                    "Apologise warmly, suggest alternative search terms or genres,\n"
                    "and optionally mention 1-2 well-known books on the topic from general\n"
                    "knowledge (clearly stating they are NOT in this library)."
                )
        elif intent == "book_knowledge":
            sections.append(
                "=== Instruction ===\n"
                "Answer this book/literary question from your general knowledge.\n"
                "Be accurate, engaging, and if relevant, invite the patron to search\n"
                "the LibraryMind catalogue for related titles."
            )
        else:  # general / off-topic
            sections.append(
                "=== Instruction ===\n"
                "This question is outside your scope as a library book assistant.\n"
                "Politely redirect the patron back to books and reading topics."
            )

        sections.append(f"=== Patron's Message ===\n{message}\n\nLibrarian (Mira) Response:")
        return "\n\n".join(sections)

    def _resolve_active_model(self) -> str:
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        return model_map.get(self.settings.PRIMARY_PROVIDER, self.settings.OPENAI_MODEL)
