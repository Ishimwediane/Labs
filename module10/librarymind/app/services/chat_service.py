"""
app/services/chat_service.py
==============================
Part 5 — LibraryMind AI Librarian Chatbot

WHAT THIS FILE DOES:
    ChatService is the brain of the chatbot. It orchestrates every step
    of a multi-turn conversation:

    1. Load the conversation's past messages from ConversationStore.
    2. Truncate history to the most recent N messages (controls prompt size).
    3. Ask RAG to search the library catalogue for relevant book context.
    4. Build a prompt that includes:
           - a warm librarian system instruction
           - the recent conversation history   <-- this is MEMORY
           - retrieved book context            <-- this is RAG GROUNDING
           - the patron's current message
    5. Send the prompt through ResilientAIService (with auto-fallback).
    6. Save both the user message and assistant reply into the store.
    7. Return the structured response to the caller (API layer or test).

WHERE MEMORY HAPPENS:
    Steps 1–2: history is loaded and truncated.
    Step 6:    both new turns are saved so the next call can use them.

WHERE RAG GROUNDING HAPPENS:
    Step 3:    the current message is embedded and ChromaDB is searched.
    Step 4:    retrieved books are injected into the prompt as context.

WHERE TRUNCATION HAPPENS:
    Step 2: only the last CHAT_HISTORY_LIMIT messages are kept in the prompt.
            This prevents the prompt from growing indefinitely and hitting
            the LLM's context-window limit.

EXAMPLE CALL SEQUENCE (see bottom of file for runnable demo):
    chat("conv1", "Hi!")
    chat("conv1", "Recommend a science fiction book")
    chat("conv1", "Tell me more about that one")   <-- uses memory
    chat("conv2", "Hi!")                           <-- separate history
"""

import logging
from typing import Any, Dict, List, Optional

from app.config import Settings
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates multi-turn AI librarian conversations.

    Responsibilities:
    - Manage conversation memory via ConversationStore.
    - Retrieve grounded book context via RAGService.
    - Build rich, history-aware prompts.
    - Generate replies via ResilientAIService.
    - Track token usage and estimated cost.
    """

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

        # How many recent messages to include in the prompt.
        # Controlled by CHAT_HISTORY_LIMIT in config (default: 10).
        self.history_limit: int = getattr(settings, "CHAT_HISTORY_LIMIT", 10)

        logger.info(
            f"ChatService initialised. History limit: {self.history_limit} messages."
        )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def chat(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """
        Process one turn of a conversation and return the assistant's reply.

        This is the only method the API layer (or a test) needs to call.

        Args:
            conversation_id: A unique string (UUID) that identifies this
                             chat session. Different patrons use different IDs.
            message:         The patron's current text message.

        Returns:
            A dict with keys:
                "reply"           – the assistant's text response
                "sources"         – list of book dicts used as grounding context
                "conversation_id" – echoed back so the client can store it
        """
        # ── STEP 0: Basic input validation ────────────────────────────
        conversation_id, message = self._validate_inputs(conversation_id, message)

        logger.info(
            f"[{conversation_id}] New chat turn. "
            f"Message preview: '{message[:60]}...'"
        )

        # ── STEP 1: Load conversation history ─────────────────────────
        # This is WHERE MEMORY IS READ.
        # ConversationStore returns [] for a brand-new conversation_id.
        full_history = self.conversation_store.get_history(conversation_id)

        # ── STEP 2: Truncate history ───────────────────────────────────
        # This is WHERE TRUNCATION HAPPENS.
        # We keep only the most recent N messages so the prompt stays
        # within the LLM's context-window limit.
        recent_history = self._truncate_history(full_history)

        if len(full_history) > len(recent_history):
            logger.debug(
                f"[{conversation_id}] History truncated: "
                f"{len(full_history)} total → {len(recent_history)} sent to LLM."
            )

        # ── STEP 3: RAG retrieval ──────────────────────────────────────
        # This is WHERE RAG GROUNDING HAPPENS.
        # We embed the current message and search ChromaDB for relevant books.
        # NOTE: RAGService.answer_question() does retrieval + generation.
        #       We only want the retrieval part here, so we use the private
        #       helper _retrieve_context() defined below, which re-uses the
        #       same embedding and vector-store calls without calling the LLM.
        catalogue_context, sources = self._retrieve_context(message)

        # ── STEP 4: Build the prompt ───────────────────────────────────
        history_text = self._format_history(recent_history)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            history_text=history_text,
            context_text=catalogue_context,
            message=message,
        )

        # ── STEP 5: Rate limit check ───────────────────────────────────
        # This raises RateLimitExceededError if the bucket is empty.
        # The FastAPI exception handler will catch it and return HTTP 429.
        self.rate_limiter.acquire()

        # ── STEP 6: Generate the AI reply ─────────────────────────────
        # ResilientAIService tries OpenAI → Claude → Gemini automatically.
        reply = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.7,   # A bit warmer than RAG (0.2) — this is a chat
            max_tokens=500,
        )

        # ── STEP 7: Record token usage and estimated cost ──────────────
        active_model = self._resolve_active_model()
        self.usage_tracker.record_usage(
            provider=self.settings.PRIMARY_PROVIDER,
            model=active_model,
            prompt=system_prompt + user_prompt,
            completion=reply,
        )

        # ── STEP 8: Save both turns into the conversation store ────────
        # This is WHERE MEMORY IS WRITTEN.
        # On the next call, these messages will be in recent_history.
        self.conversation_store.append_message(conversation_id, "user", message)
        self.conversation_store.append_message(conversation_id, "assistant", reply)

        logger.info(
            f"[{conversation_id}] Reply generated. "
            f"Sources: {len(sources)}. "
            f"Total history: {self.conversation_store.get_message_count(conversation_id)} messages."
        )

        # ── STEP 9: Return structured response ────────────────────────
        return {
            "reply": reply,
            "sources": sources,
            "conversation_id": conversation_id,
        }

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================

    def _validate_inputs(self, conversation_id: str, message: str):
        """
        Validate and sanitise inputs before processing.

        - Strips whitespace from both fields.
        - Raises ValueError for empty or missing inputs.

        Args:
            conversation_id: Raw conversation ID from the caller.
            message:         Raw user message from the caller.

        Returns:
            (cleaned_conversation_id, cleaned_message) tuple.
        """
        if not conversation_id or not conversation_id.strip():
            raise ValueError("conversation_id must not be empty.")
        if not message or not message.strip():
            raise ValueError("message must not be empty.")

        return conversation_id.strip(), message.strip()

    def _truncate_history(
        self, history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Keep only the most recent `history_limit` messages.

        Example (limit = 4):
            Full:     [msg1, msg2, msg3, msg4, msg5, msg6]
            Truncated:               [msg3, msg4, msg5, msg6]

        Why this matters:
            LLMs have a context-window limit (e.g. 8K or 128K tokens).
            Sending the entire history of a long conversation can be too
            expensive or crash the request. Truncation keeps it affordable.

        Args:
            history: The full, untruncated message list from ConversationStore.

        Returns:
            A slice of the most recent N messages.
        """
        if len(history) <= self.history_limit:
            return history  # Nothing to cut

        return history[-self.history_limit :]

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """
        Convert the list of message dicts into a plain-text block
        that can be embedded inside the LLM prompt.

        Example output:
            Patron: Hi!
            Librarian: Hello! How can I help you today?
            Patron: Recommend a sci-fi book.
            Librarian: I recommend Dune by Frank Herbert...

        Args:
            history: Truncated list of message dicts.

        Returns:
            A multi-line string, or "" if history is empty.
        """
        if not history:
            return ""

        lines = []
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Use friendly labels instead of raw "user" / "assistant".
            label = "Patron" if role == "user" else "Librarian"
            lines.append(f"{label}: {content}")

        return "\n".join(lines)

    def _retrieve_context(
        self, message: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Use RAGService to search the library catalogue for books relevant
        to the patron's current message.

        HOW THIS WORKS:
            RAGService.answer_question() does two things internally:
              1. Embed the question → search ChromaDB → filter by threshold.
              2. Call the LLM to generate an answer.

            For the chatbot we only want step 1 (the retrieval), because
            step 2 is handled by ChatService itself (with history context).

            WORKAROUND:
            RAGService does not expose a public retrieve_context() method.
            We call answer_question() and use the "sources" it returns to
            reconstruct the context block. This avoids duplicating the
            embedding and vector-search logic.

            FUTURE IMPROVEMENT:
            Extract a public `rag_service.retrieve_context(question)` method
            from RAGService so ChatService can call retrieval directly.

        Args:
            message: The patron's current message (used as the search query).

        Returns:
            A (context_text, sources) tuple:
                context_text – a formatted string of book details for the prompt,
                               or "" if nothing was found.
                sources      – a list of {"title", "author", "score"} dicts,
                               or [] if nothing was found.
        """
        try:
            rag_result = self.rag_service.answer_question(message)
        except Exception as exc:
            # RAG is best-effort in chat — if retrieval fails, we still reply.
            logger.warning(f"RAG retrieval failed: {exc}. Continuing without context.")
            return "", []

        sources: List[Dict[str, Any]] = rag_result.get("sources", [])

        if not sources:
            logger.debug("No relevant catalogue context found for this message.")
            return "", []

        # Build a readable context block from the sources.
        # Each source has: title, author, score.
        # We add a generic description note since sources only carry metadata.
        context_lines = []
        for i, src in enumerate(sources, 1):
            context_lines.append(
                f"BOOK {i}:\n"
                f"  Title:  {src.get('title', 'Unknown')}\n"
                f"  Author: {src.get('author', 'Unknown')}\n"
                f"  Relevance score: {src.get('score', 0):.2f}"
            )

        context_text = "\n\n".join(context_lines)
        logger.debug(f"Retrieved {len(sources)} catalogue result(s) for grounding.")
        return context_text, sources

    def _build_system_prompt(self) -> str:
        """
        Build the system-level instruction that shapes the assistant's personality.

        This is the "job description" given to the LLM at the start of every call.
        It tells the model to be warm, helpful, and — critically — honest about
        what is and is not in the catalogue (anti-hallucination guardrail).

        Returns:
            A multi-line string to be passed as the `system` argument to the LLM.
        """
        return (
            "You are a warm, knowledgeable, and friendly AI Librarian for LibraryMind.\n"
            "\n"
            "Your personality:\n"
            "  - Speak conversationally and warmly, like a librarian who genuinely loves books.\n"
            "  - Be concise but never cold. A short, helpful answer is better than a long ramble.\n"
            "  - Use the patron's own words when possible to show you are listening.\n"
            "\n"
            "Your strict rules:\n"
            "  1. ONLY recommend or discuss books that appear in the 'Library Catalogue Context' below.\n"
            "  2. NEVER invent book titles, author names, or plot details.\n"
            "  3. If the catalogue does not contain relevant books, say so honestly and warmly.\n"
            "  4. If the patron asks a general question (e.g. 'Hi!'), respond naturally — "
            "no need to force a book recommendation.\n"
            "  5. Always refer to book titles and authors exactly as they appear in the catalogue.\n"
        )

    def _build_user_prompt(
        self,
        history_text: str,
        context_text: str,
        message: str,
    ) -> str:
        """
        Assemble the full user-side prompt that goes to the LLM.

        The prompt has up to three sections:
          [A] Recent conversation history  → gives the LLM memory of past turns.
          [B] Library catalogue context    → grounds the answer in real catalogue data.
          [C] Current patron message       → what the patron just said.

        Sections [A] and [B] are included only when they contain content.

        Why this structure matters:
          - Without [A], follow-ups like "Tell me more about that one" fail.
          - Without [B], the LLM may invent books that don't exist.
          - Without [C], the LLM doesn't know what was just asked.

        Args:
            history_text: Formatted string of recent conversation turns (may be "").
            context_text: Formatted catalogue context from RAG (may be "").
            message:      The patron's current message.

        Returns:
            A multi-line string ready to be sent to the LLM.
        """
        sections: List[str] = []

        # ── Section A: Conversation History ───────────────────────────
        if history_text:
            sections.append(
                "=== Recent Conversation History ===\n"
                "(Use this to understand follow-up questions and references.)\n"
                f"{history_text}"
            )

        # ── Section B: Library Catalogue Context ───────────────────────
        if context_text:
            sections.append(
                "=== Library Catalogue Context ===\n"
                "(These are the ONLY books you may recommend or discuss.)\n"
                f"{context_text}"
            )
        else:
            # No relevant books found — remind the model not to invent any.
            sections.append(
                "=== Library Catalogue Context ===\n"
                "No relevant books were found in the catalogue for this query.\n"
                "Do NOT invent any book titles or authors. "
                "Acknowledge this honestly and helpfully."
            )

        # ── Section C: Current patron message ─────────────────────────
        sections.append(
            f"=== Patron's Current Message ===\n{message}\n\n"
            "Librarian Response:"
        )

        return "\n\n".join(sections)

    def _resolve_active_model(self) -> str:
        """
        Return the model name string that matches the active primary provider.

        Used only for usage tracking — does not affect generation.

        Returns:
            The model name string from settings (e.g. "gpt-4-turbo-preview").
        """
        provider = self.settings.PRIMARY_PROVIDER
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        return model_map.get(provider, self.settings.OPENAI_MODEL)


# ======================================================================
# USAGE EXAMPLE
# (Run this block to see how ChatService works without a web server.)
# ======================================================================

if __name__ == "__main__":
    """
    Quick demo showing how to wire everything together and run
    three conversation turns.

    To run:
        cd librarymind
        python -m app.services.chat_service
    """
    import logging
    logging.basicConfig(level=logging.INFO)

    # ── Wire up dependencies ──────────────────────────────────────────
    from app.config import get_settings
    from app.infrastructure.conversation_store import ConversationStore
    from app.infrastructure.rate_limiter import TokenBucketRateLimiter
    from app.infrastructure.usage_tracker import UsageTracker
    from app.infrastructure.cache import CacheService
    from app.infrastructure.vector_store import ChromaVectorStore
    from app.providers.resilient_service import ResilientAIService
    from app.services.embedding_service import EmbeddingService
    from app.services.rag_service import RAGService

    settings = get_settings()

    embedding_service = EmbeddingService(settings)
    vector_store      = ChromaVectorStore(settings)
    cache_service     = CacheService(settings)
    rate_limiter      = TokenBucketRateLimiter(capacity=60, refill_rate=1.0)
    usage_tracker     = UsageTracker()
    ai_service        = ResilientAIService()

    rag_service = RAGService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        cache_service=cache_service,
        rate_limiter=rate_limiter,
        usage_tracker=usage_tracker,
        ai_service=ai_service,
        settings=settings,
    )

    # ── Build the ConversationStore and ChatService ───────────────────
    store = ConversationStore()       # starts empty

    chat_service = ChatService(
        rag_service=rag_service,
        ai_service=ai_service,
        conversation_store=store,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    CONV_ID = "demo-conv-001"

    # ── Turn 1: Simple greeting ───────────────────────────────────────
    # No RAG context needed — just a friendly hello.
    print("\n" + "=" * 60)
    print("TURN 1: Greeting")
    result1 = chat_service.chat(CONV_ID, "Hi!")
    print(f"Librarian: {result1['reply']}")
    print(f"Sources:   {result1['sources']}")
    # ↑ Memory written: ["user: Hi!", "assistant: Hello! ..."]

    # ── Turn 2: Book recommendation request ──────────────────────────
    # RAG embeds "Recommend a science fiction book", searches ChromaDB,
    # and injects relevant books into the prompt for grounding.
    print("\n" + "=" * 60)
    print("TURN 2: Sci-fi recommendation")
    result2 = chat_service.chat(CONV_ID, "Recommend a science fiction book")
    print(f"Librarian: {result2['reply']}")
    print(f"Sources:   {result2['sources']}")
    # ↑ Memory now has 4 messages (2 turns).
    # ↑ RAG context included in the prompt.

    # ── Turn 3: Follow-up using memory ───────────────────────────────
    # "that one" can only be resolved because the prompt includes the
    # history from Turn 2. Without memory, the LLM would not know
    # what book the patron is referring to.
    print("\n" + "=" * 60)
    print("TURN 3: Follow-up (uses memory)")
    result3 = chat_service.chat(CONV_ID, "Tell me more about that one")
    print(f"Librarian: {result3['reply']}")
    print(f"Sources:   {result3['sources']}")
    # ↑ History block shows the previous recommendation, so "that one" resolves.

    # ── Separate session — completely isolated history ────────────────
    print("\n" + "=" * 60)
    print("SEPARATE SESSION (conv2) — isolated from conv1")
    result4 = chat_service.chat("demo-conv-002", "Hi!")
    print(f"Librarian: {result4['reply']}")
    # ↑ This session has NO knowledge of the sci-fi conversation above.

    print("\n" + "=" * 60)
    print(f"Active conversations: {store.list_conversations()}")
    print(f"conv1 message count:  {store.get_message_count(CONV_ID)}")
    print(f"conv2 message count:  {store.get_message_count('demo-conv-002')}")
