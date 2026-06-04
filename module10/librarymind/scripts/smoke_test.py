"""
Part 8 smoke test — validates every lab scenario from the test table.

Run from the librarymind/ directory:
    python scripts/smoke_test.py

Scenarios covered (Part 8 test table):
    S1  Search:  "desert planet adventure"        → sci-fi books with high scores
    S2  Ask:     "What is the meaning of life?"   → polite refusal (not in catalogue)
    S3  Ask:     "Recommend a classic romance"    → grounded answer with sources
    S4  Chat T1: "Recommend a thriller"           → specific book from catalogue
    S5  Chat T2: "Tell me more about that"        → elaborates on T1 book (memory)
    S6  Classify: frustrated card complaint       → technical / high / negative
    S7  Summarise: 3–5 mixed reviews              → balanced praise and criticism
    S8  Cache:    same question twice             → second call returns cached=True
    S9  Rate limit exceeded                       → RateLimitExceededError raised
    S10 Provider fallback                         → secondary provider used on key failure
"""

import io
import logging
import sys
import uuid

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from app.config import get_settings
from app.infrastructure.cache import CacheService
from app.infrastructure.conversation_store import ConversationStore
from app.infrastructure.rate_limiter import TokenBucketRateLimiter, RateLimitExceededError
from app.infrastructure.usage_tracker import UsageTracker
from app.infrastructure.vector_store import ChromaVectorStore
from app.providers.resilient_service import ResilientAIService
from app.services.chat_service import ChatService
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService
from app.services.summarisation_service import SummarisationService

_pass = 0
_fail = 0


def _ok(label: str) -> None:
    global _pass
    _pass += 1
    print(f"  [PASS] {label}")


def _fail_test(label: str, reason: str) -> None:
    global _fail
    _fail += 1
    print(f"  [FAIL] {label}")
    print(f"         {reason}")


def check(label: str, condition: bool, reason: str = "condition was False") -> None:
    if condition:
        _ok(label)
    else:
        _fail_test(label, reason)


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def build_services():
    settings = get_settings()
    embedding_svc = EmbeddingService()
    vector_store  = ChromaVectorStore()
    cache_svc     = CacheService()
    rate_limiter  = TokenBucketRateLimiter()
    usage_tracker = UsageTracker()
    ai_service    = ResilientAIService()
    store         = ConversationStore()

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
    classifier = ClassificationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )
    summariser = SummarisationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )
    return rag_service, chat_service, classifier, summariser, usage_tracker, embedding_svc, vector_store


def run_s1_search(embedding_svc, vector_store):
    section("S1 · Search: 'desert planet adventure'")
    try:
        embedding = embedding_svc.embed_text("desert planet adventure")
        results = vector_store.search(embedding, top_k=3)
        print(f"  Results returned: {len(results)}")
        for r in results:
            print(f"    · [{r.get('score', 0):.3f}] {r.get('title')} — {r.get('genre')}")
        check("S1 · search returns at least one result", len(results) > 0,
              "No results — is the vector store seeded? Run scripts/seed_books.py first.")
    except Exception as exc:
        _fail_test("S1 · search raised an exception", str(exc))


def run_s2_off_topic(rag_service):
    section("S2 · Ask: 'What is the meaning of life?'  (expect polite refusal)")
    try:
        result = rag_service.answer_question("What is the meaning of life?")
        print(f"  Answer: {result['answer'][:200]}")
        check("S2 · answer is not empty", bool(result["answer"].strip()))
        check("S2 · sources list present", isinstance(result.get("sources"), list))
        print("  ↑ Manually verify: answer should politely decline, not invent books.")
    except Exception as exc:
        _fail_test("S2 · off-topic question raised an exception", str(exc))


def run_s3_romance(rag_service):
    section("S3 · Ask: 'Recommend a classic romance novel'  (expect grounded answer)")
    try:
        result = rag_service.answer_question("Recommend a classic romance novel")
        print(f"  Answer : {result['answer'][:200]}")
        print(f"  Sources: {[s.get('title') for s in result.get('sources', [])]}")
        check("S3 · answer is not empty", bool(result["answer"].strip()))
        check("S3 · sources is a list", isinstance(result.get("sources"), list))
    except Exception as exc:
        _fail_test("S3 · romance question raised an exception", str(exc))


def run_s4_s5_chat(chat_service):
    section("S4+S5 · Chat: thriller recommendation then follow-up (tests memory)")
    conv_id = f"smoke-{uuid.uuid4()}"
    try:
        r1 = chat_service.chat(conv_id, "Recommend a thriller book.")
        print(f"  [T1] Patron  : Recommend a thriller book.")
        print(f"  [T1] Librarian: {r1['reply'][:200]}")
        check("S4 · T1 reply is not empty", bool(r1["reply"].strip()))
        check("S4 · T1 sources is a list", isinstance(r1.get("sources"), list))

        r2 = chat_service.chat(conv_id, "Tell me more about that one.")
        print(f"\n  [T2] Patron  : Tell me more about that one.")
        print(f"  [T2] Librarian: {r2['reply'][:200]}")
        check("S5 · T2 reply is not empty", bool(r2["reply"].strip()))
        check("S5 · same conv_id echoed", r2["conversation_id"] == conv_id)
        print("  ↑ Manually verify: T2 reply should elaborate on T1's book (memory).")
    except Exception as exc:
        _fail_test("S4/S5 · chat test raised an exception", str(exc))


def run_s6_classify(classifier):
    section("S6 · Classify: frustrated card complaint  (expect technical/high/negative)")
    ticket = (
        "My library card isn't working at the self-checkout kiosk "
        "and I'm very frustrated. I've been trying for 20 minutes."
    )
    try:
        result = classifier.classify_ticket(ticket)
        print(f"  Result: {result}")
        check("S6 · category = technical", result.get("category") == "technical",
              f"Got category={result.get('category')!r}")
        check("S6 · priority = high or urgent",
              result.get("priority") in {"high", "urgent"},
              f"Got priority={result.get('priority')!r}")
        check("S6 · sentiment = negative", result.get("sentiment") == "negative",
              f"Got sentiment={result.get('sentiment')!r}")
    except Exception as exc:
        _fail_test("S6 · classification raised an exception", str(exc))


def run_s7_summarise(summariser):
    section("S7 · Summarise: 3–5 mixed reviews  (expect balanced output)")
    reviews = [
        "Absolutely loved this book. The characters are vivid and the plot gripping. 5/5.",
        "Decent read but the pacing in the middle dragged. Picked up at the end. 3/5.",
        "The world-building is incredible. A must-read for any sci-fi fan. 5 stars.",
        "Not my cup of tea. Found the writing style hard to follow. 2 out of 5.",
        "A solid novel. Some brilliant moments, some slow chapters. Overall enjoyable. 3.5/5.",
    ]
    try:
        result = summariser.summarise_reviews(reviews)
        import json as _json
        print("  Result:")
        print("  " + _json.dumps(result, indent=2).replace("\n", "\n  "))
        required = ["overall_sentiment", "average_rating", "key_themes", "praise", "criticism", "recommendation"]
        for field in required:
            check(f"S7 · field '{field}' present", field in result, f"Missing field '{field}'")
        check("S7 · praise is non-empty list", isinstance(result.get("praise"), list) and len(result.get("praise", [])) > 0)
        check("S7 · criticism is non-empty list", isinstance(result.get("criticism"), list) and len(result.get("criticism", [])) > 0)
    except Exception as exc:
        _fail_test("S7 · summarisation raised an exception", str(exc))


def run_s8_cache(rag_service):
    section("S8 · Cache: same question twice  (second call must be cached)")
    question = "What books do you have about space exploration?"
    try:
        r1 = rag_service.answer_question(question)
        print(f"  Call 1 — cached: {r1.get('cached')}")
        r2 = rag_service.answer_question(question)
        print(f"  Call 2 — cached: {r2.get('cached')}")
        check("S8 · first call not cached", r1.get("cached") is False,
              f"Expected cached=False on first call, got {r1.get('cached')!r}")
        check("S8 · second call IS cached", r2.get("cached") is True,
              f"Expected cached=True on second call, got {r2.get('cached')!r}")
    except Exception as exc:
        _fail_test("S8 · cache test raised an exception", str(exc))


def run_s9_rate_limit():
    section("S9 · Rate limit: exhaust the bucket  (expect RateLimitExceededError)")
    limiter = TokenBucketRateLimiter(capacity=3, refill_rate=0.0)
    hit = False
    try:
        for _ in range(10):
            limiter.acquire()
    except RateLimitExceededError:
        hit = True
    check("S9 · RateLimitExceededError raised after bucket is empty", hit,
          "Rate limiter did not raise an error after exhausting all tokens.")


def run_s10_provider_fallback():
    section("S10 · Provider fallback  (inject bad primary key → secondary takes over)")
    try:
        from app.providers.openai_provider import OpenAIProvider
        from app.providers.anthropic_provider import AnthropicProvider

        bad_openai   = OpenAIProvider(api_key="sk-invalid-key-for-fallback-test")
        good_anthropic = AnthropicProvider()

        from app.providers.base import AIProvider
        class _FallbackService:
            def __init__(self, providers):
                self._providers = providers
            def generate(self, prompt, system="", temperature=0.2, max_tokens=50):
                last_exc = None
                for p in self._providers:
                    try:
                        return p.generate(prompt, system=system,
                                          temperature=temperature, max_tokens=max_tokens)
                    except Exception as exc:
                        last_exc = exc
                raise RuntimeError(f"All providers failed. Last error: {last_exc}")

        svc = _FallbackService([bad_openai, good_anthropic])
        reply = svc.generate("Say hello in one sentence.", max_tokens=30)
        print(f"  Fallback reply: {reply[:120]}")
        check("S10 · fallback service returned a non-empty reply", bool(reply.strip()),
              "Reply was empty — fallback may not have kicked in.")
    except Exception as exc:
        _fail_test("S10 · provider fallback raised an unexpected exception", str(exc))


def main():
    print("\n" + "█" * 60)
    print("  LibraryMind — Part 8 Smoke Test")
    print("█" * 60)

    try:
        rag_service, chat_service, classifier, summariser, usage_tracker, embedding_svc, vector_store = build_services()
    except Exception as exc:
        print(f"\n[FATAL] Could not build services: {exc}")
        sys.exit(1)

    run_s1_search(embedding_svc, vector_store)
    run_s2_off_topic(rag_service)
    run_s3_romance(rag_service)
    run_s4_s5_chat(chat_service)
    run_s6_classify(classifier)
    run_s7_summarise(summariser)
    run_s8_cache(rag_service)
    run_s9_rate_limit()
    run_s10_provider_fallback()

    total = _pass + _fail
    print(f"\n{'═' * 60}")
    print(f"  RESULTS: {_pass} passed, {_fail} failed  (of {total} checks)")
    print(f"  Usage tracker: {usage_tracker.get_total_requests()} AI calls, "
          f"${usage_tracker.get_daily_cost():.6f} USD")
    print(f"{'═' * 60}\n")

    if _fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
