"""
PURPOSE:
    Validates that ChatService works correctly end-to-end.
 
WHAT IS TESTED:
    Test 1 — Greeting:          A simple "Hi!" should get a warm reply, no sources.
    Test 2 — RAG grounding:     A book query should return a grounded answer with sources.
    Test 3 — Memory / follow-up: "Tell me more about that one" should resolve via history.
    Test 4 — Off-catalogue:     A query with no catalogue match should NOT invent books.
    Test 5 — Isolation:         A new conversation_id starts with zero history.
    Test 6 — Memory integrity:  Correct number of messages saved after 3 turns.

"""

import io
import logging
import sys
import uuid

# Fix Windows terminal encoding so test output prints cleanly.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.config import get_settings
from app.infrastructure.cache import CacheService
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.infrastructure.vector_store import ChromaVectorStore
from app.providers.resilient_service import ResilientAIService
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

# Logging 
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Helpers


def print_separator(title: str) -> None:
    """Print a clearly labelled section divider."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(turn: int, message: str, result: dict) -> None:
    """Print one conversation turn in a readable format."""
    print(f"\n[TURN {turn}] Patron: {message}")
    print(f"  Librarian : {result['reply']}")
    sources = result.get("sources", [])
    if sources:
        print(f"  Sources   : {[s['title'] for s in sources]}")
    else:
        print(f"  Sources   : (none)")
    print(f"  Conv ID   : {result['conversation_id']}")


def assert_equal(label: str, actual, expected) -> None:
    """Simple assertion that prints PASS or FAIL."""
    if actual == expected:
        print(f"  [PASS] {label}")
    else:
        print(f"  [FAIL] {label}")
        print(f"       Expected : {expected}")
        print(f"       Got      : {actual}")


def assert_true(label: str, condition: bool) -> None:
    """Simple boolean assertion."""
    if condition:
        print(f"  [PASS] {label}")
    else:
        print(f"  [FAIL] {label}")


# Dependency wiring


def build_chat_service() -> tuple[ChatService, ConversationStore, UsageTracker]:
    """
    Instantiate all dependencies and return a ready-to-use ChatService.

    Returns:
        (chat_service, conversation_store, usage_tracker) tuple so tests
        can inspect the store and tracker directly.
    """
    logger.info("Wiring up dependencies...")
    settings = get_settings()

    embedding_svc  = EmbeddingService()
    vector_store   = ChromaVectorStore()
    cache_svc      = CacheService()
    rate_limiter   = TokenBucketRateLimiter()
    usage_tracker  = UsageTracker()
    ai_service     = ResilientAIService()
    store          = ConversationStore()

    rag_service = RAGService(
        embedding_service=embedding_svc,
        vector_store=vector_store,
        cache_service=cache_svc,
        rate_limiter=rate_limiter,
        usage_tracker=usage_tracker,
        ai_service=ai_service,
        settings=settings,
    )

    chat_service = ChatService(
        rag_service=rag_service,
        ai_service=ai_service,
        conversation_store=store,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    logger.info("All dependencies ready.")
    return chat_service, store, usage_tracker


# Individual tests


def test_greeting(chat_service: ChatService, conv_id: str) -> None:
    """
    Test 1 — Greeting
    A simple "Hi!" should get a warm natural reply.
    No book recommendation is expected for a greeting.
    """
    print_separator("TEST 1: Greeting")

    result = chat_service.chat(conv_id, "Hi!")
    print_result(1, "Hi!", result)

    assert_true("Reply is not empty",   bool(result["reply"].strip()))
    assert_equal("conversation_id echoed", result["conversation_id"], conv_id)

    print("\n  → A warm greeting reply proves the chatbot starts naturally.")


def test_rag_grounded_recommendation(chat_service: ChatService, conv_id: str) -> None:
    """
    Test 2 — RAG-grounded recommendation
    A specific book request should produce an answer sourced from the catalogue.
    The reply must not be empty and sources should be populated when books match.
    """
    print_separator("TEST 2: RAG-grounded Book Recommendation")

    message = "Recommend a science fiction book about survival on a desert planet."
    result = chat_service.chat(conv_id, message)
    print_result(2, message, result)

    assert_true("Reply is not empty", bool(result["reply"].strip()))
    assert_true(
        "Sources list is a list",
        isinstance(result["sources"], list),
    )
    # Sources may be empty if no books crossed the relevance threshold.
    # We do NOT hard-assert sources here — that depends on the seeded catalogue.
    if result["sources"]:
        print(f"  [PASS] Grounded: {len(result['sources'])} source(s) returned.")
    else:
        print(
            "  [INFO] No sources above threshold. "
            "Check that books.json is seeded into ChromaDB."
        )

    print("\n  → A grounded reply proves RAG retrieval was wired into the chat prompt.")


def test_followup_uses_memory(chat_service: ChatService, conv_id: str) -> None:
    """
    Test 3 — Follow-up resolved via conversation memory
    After recommending a book in Test 2, "Tell me more about that one"
    should produce a relevant reply — not a confused or generic response.
    This works ONLY because the history block is included in the prompt.
    """
    print_separator("TEST 3: Follow-up Using Conversation Memory")

    message = "Tell me more about that one."
    result = chat_service.chat(conv_id, message)
    print_result(3, message, result)

    assert_true("Follow-up reply is not empty", bool(result["reply"].strip()))
    assert_equal("conversation_id unchanged", result["conversation_id"], conv_id)

    print(
        "\n  → If the librarian's reply references the earlier book, "
        "memory is working correctly."
    )


def test_no_catalogue_match(chat_service: ChatService, conv_id: str) -> None:
    """
    Test 4 — No relevant catalogue results
    A query completely outside the catalogue should NOT invent books.
    The chatbot should acknowledge it cannot help rather than hallucinate.
    """
    print_separator("TEST 4: Off-Catalogue Query (Anti-Hallucination)")

    # This is intentionally obscure — very unlikely to match any seeded book.
    message = (
        "Can you recommend a 16th-century Ottoman military strategy manual "
        "written in Middle Persian?"
    )
    result = chat_service.chat(conv_id, message)
    print_result(4, message, result)

    assert_true("Reply is not empty", bool(result["reply"].strip()))
    # We cannot assert exact wording, but we print a reminder of the expected behaviour.
    print(
        "\n  → The librarian should say it cannot find relevant books, "
        "NOT invent titles. Read the reply above to verify."
    )


def test_conversation_isolation(chat_service: ChatService, store: ConversationStore) -> None:
    """
    Test 5 — Conversation isolation
    A brand-new conversation_id must start with zero history,
    completely independent of any other session.
    """
    print_separator("TEST 5: Conversation Isolation (Separate IDs)")

    new_conv_id = f"isolation-test-{uuid.uuid4()}"

    # The new session should start with empty history.
    history_before = store.get_history(new_conv_id)
    assert_equal("New session starts with 0 messages", len(history_before), 0)

    result = chat_service.chat(new_conv_id, "Hi there!")
    print_result(1, "Hi there!", result)

    # After one turn, exactly 2 messages (user + assistant) should exist.
    history_after = store.get_history(new_conv_id)
    assert_equal("After 1 turn, 2 messages stored", len(history_after), 2)
    assert_equal("First message role is 'user'",      history_after[0]["role"], "user")
    assert_equal("Second message role is 'assistant'", history_after[1]["role"], "assistant")

    print(
        "\n  → Different conversation IDs maintain completely separate histories."
    )


def test_memory_integrity(
    store: ConversationStore,
    conv_id: str,
    expected_turns: int,
) -> None:
    """
    Test 6 — Memory integrity
    After N conversation turns, the store should hold exactly N*2 messages
    (one user + one assistant per turn).
    """
    print_separator("TEST 6: Memory Integrity Check")

    stored = store.get_history(conv_id)
    expected_msg_count = expected_turns * 2  # user + assistant per turn

    print(f"  Conversation ID  : {conv_id}")
    print(f"  Expected turns   : {expected_turns}")
    print(f"  Expected messages: {expected_msg_count}")
    print(f"  Actual messages  : {len(stored)}")

    assert_equal(
        f"Stored message count equals {expected_msg_count}",
        len(stored),
        expected_msg_count,
    )

    # Verify alternating roles: user, assistant, user, assistant, ...
    for i, msg in enumerate(stored):
        expected_role = "user" if i % 2 == 0 else "assistant"
        assert_equal(
            f"Message {i + 1} role",
            msg["role"],
            expected_role,
        )

    print(
        "\n  → Correct alternating roles confirm that both user and assistant "
        "messages are being saved after every turn."
    )


# =====================================================================
# Main runner
# =====================================================================

def run_all_tests() -> None:
    """
    Wire dependencies, then run all six tests in sequence.
    Tests 1–4 share one conversation_id to exercise memory across turns.
    Tests 5–6 use a separate session to verify isolation and integrity.
    """
    chat_service, store, usage_tracker = build_chat_service()

    # A single shared conversation ID for tests 1 to 4.
    CONV_A = f"part5-test-{uuid.uuid4()}"

    # ── Run tests ────────────────────────────────────────────────────
    test_greeting(chat_service, CONV_A)                     # Turn 1
    test_rag_grounded_recommendation(chat_service, CONV_A)  # Turn 2
    test_followup_uses_memory(chat_service, CONV_A)         # Turn 3 — uses memory
    test_no_catalogue_match(chat_service, CONV_A)           # Turn 4

    # Isolation test uses a completely fresh session internally.
    test_conversation_isolation(chat_service, store)

    # After tests 1–4, conv_A should have exactly 4 turns → 8 messages.
    test_memory_integrity(store, CONV_A, expected_turns=4)

    # ── Final cost report ─────────────────────────────────────────────
    print_separator("SESSION COST SUMMARY")
    print(f"  Total requests : {usage_tracker.get_total_requests()}")
    print(f"  Estimated cost : ${usage_tracker.get_daily_cost():.6f} USD")
    print()


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        logger.error(f"Test run failed with exception: {e}", exc_info=True)
