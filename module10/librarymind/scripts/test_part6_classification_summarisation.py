"""
scripts/test_part6_classification_summarisation.py
====================================================
Part 6 — LibraryMind Classification & Summarisation

PURPOSE:
    Validates that all Part 6 components work correctly — both in
    isolation (unit tests, no AI calls) and end-to-end (live AI calls).

WHAT IS TESTED:
    ── Unit Tests (no AI calls, always fast) ────────────────────────────
    Test U1  — strip_markdown_fences: plain JSON passes through unchanged
    Test U2  — strip_markdown_fences: ```json … ``` fences are stripped
    Test U3  — strip_markdown_fences: plain ``` … ``` fences are stripped
    Test U4  — parse_json_safely: valid JSON parses correctly
    Test U5  — parse_json_safely: invalid JSON raises ValueError
    Test U6  — validate_required_keys: all present → no error
    Test U7  — validate_required_keys: missing key → clear ValueError
    Test U8  — extract_json: full pipeline works on fenced JSON
    Test U9  — ClassificationService: empty input raises ValueError
    Test U10 — ClassificationService: too-short input raises ValueError
    Test U11 — SummarisationService: empty list raises ValueError
    Test U12 — SummarisationService: list over 50 raises ValueError
    Test U13 — SummarisationService: non-string item raises ValueError
    Test U14 — SummarisationService: empty string in list raises ValueError

    ── Live Integration Tests (real AI calls) ───────────────────────────
    Test L1  — ClassificationService: classify a frustrated account ticket
    Test L2  — ClassificationService: classify a low-priority suggestion
    Test L3  — ClassificationService: all output fields are present
    Test L4  — ClassificationService: category is within allowed values
    Test L5  — ClassificationService: priority is within allowed values
    Test L6  — ClassificationService: sentiment is within allowed values
    Test L7  — SummarisationService: summarise a set of positive reviews
    Test L8  — SummarisationService: all output fields are present
    Test L9  — SummarisationService: average_rating is a number (int/float)
    Test L10 — SummarisationService: key_themes, praise, criticism are lists
    Test L11 — UsageTracker: requests were recorded for both services

HOW TO RUN:
    cd librarymind
    python -m scripts.test_part6_classification_summarisation

NOTE:
    Unit tests run without any AI provider. They test the shared JSON
    pipeline and input validation logic directly.

    Live tests require at least one configured API key in .env.
    They make real calls to the AI provider and will consume tokens.
"""

import io
import logging
import sys

# ── Fix Windows terminal encoding ─────────────────────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Imports ───────────────────────────────────────────────────────────
from app.config import get_settings
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.services.classification_service import (
    ClassificationService,
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
    ALLOWED_SENTIMENTS,
)
from app.services.summarisation_service import SummarisationService
from app.utils.json_output import (
    strip_markdown_fences,
    parse_json_safely,
    validate_required_keys,
    extract_json,
)

# ── Logging ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# =====================================================================
# Test counters (global, simple)
# =====================================================================

_pass_count = 0
_fail_count = 0


# =====================================================================
# Assertion helpers
# =====================================================================

def print_separator(title: str) -> None:
    """Print a clearly labelled section divider."""
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print(f"{'=' * 64}")


def _record_pass(label: str) -> None:
    global _pass_count
    _pass_count += 1
    print(f"  [PASS] {label}")


def _record_fail(label: str, reason: str) -> None:
    global _fail_count
    _fail_count += 1
    print(f"  [FAIL] {label}")
    print(f"         Reason: {reason}")


def assert_true(label: str, condition: bool, reason: str = "") -> None:
    """Assert that a condition is True."""
    if condition:
        _record_pass(label)
    else:
        _record_fail(label, reason or "Condition was False.")


def assert_equal(label: str, actual, expected) -> None:
    """Assert that actual == expected."""
    if actual == expected:
        _record_pass(label)
    else:
        _record_fail(label, f"Expected {expected!r}, got {actual!r}.")


def assert_raises(label: str, exc_type: type, fn, *args, **kwargs) -> None:
    """Assert that calling fn(*args, **kwargs) raises exc_type."""
    try:
        fn(*args, **kwargs)
        _record_fail(label, f"Expected {exc_type.__name__} but no exception was raised.")
    except exc_type as exc:
        _record_pass(f"{label}  (got: {exc_type.__name__}: {str(exc)[:80]})")
    except Exception as exc:
        _record_fail(
            label,
            f"Expected {exc_type.__name__} but got {type(exc).__name__}: {exc}"
        )


def run_live_test(label: str, fn, *args, **kwargs):
    """
    Call fn(*args, **kwargs) and return the result.
    If any exception is raised, record it as a FAIL and return None.
    This prevents a single provider error from aborting the whole suite.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        _record_fail(label, f"{type(exc).__name__}: {str(exc)[:120]}")
        return None


# =====================================================================
# ── UNIT TESTS  (no AI calls) ────────────────────────────────────────
# =====================================================================

def run_unit_tests() -> None:
    """
    Run all unit tests.

    These tests work entirely with local Python logic. No AI provider is
    contacted. They run instantly and can be run offline.
    """
    print_separator("UNIT TESTS — JSON Output Pipeline  (app/utils/json_output.py)")

    # ── Test U1: plain JSON passes through strip_markdown_fences unchanged ──
    plain = '{"category": "account", "priority": "high"}'
    result = strip_markdown_fences(plain)
    assert_equal(
        "U1 · plain JSON is returned unchanged by strip_markdown_fences",
        result,
        plain,
    )

    # ── Test U2: ```json ... ``` fences are stripped ───────────────────────
    fenced_json = '```json\n{"category": "account"}\n```'
    result = strip_markdown_fences(fenced_json)
    assert_equal(
        "U2 · ```json fences are stripped correctly",
        result,
        '{"category": "account"}',
    )

    # ── Test U3: plain ``` ... ``` fences (no language tag) ───────────────
    fenced_plain = '```\n{"category": "account"}\n```'
    result = strip_markdown_fences(fenced_plain)
    assert_equal(
        "U3 · plain ``` fences (no language tag) are stripped correctly",
        result,
        '{"category": "account"}',
    )

    # ── Test U4: valid JSON parses to the expected dict ───────────────────
    valid_json = '{"category": "technical", "priority": "high"}'
    parsed = parse_json_safely(valid_json)
    assert_equal(
        "U4 · parse_json_safely returns correct dict for valid JSON",
        parsed,
        {"category": "technical", "priority": "high"},
    )

    # ── Test U5: invalid JSON raises ValueError ────────────────────────────
    assert_raises(
        "U5 · parse_json_safely raises ValueError on invalid JSON",
        ValueError,
        parse_json_safely,
        "This is not JSON at all.",
    )

    # ── Test U6: all required keys present → no error ─────────────────────
    data = {"category": "account", "priority": "high", "sentiment": "neutral"}
    try:
        validate_required_keys(data, ["category", "priority", "sentiment"])
        _record_pass("U6 · validate_required_keys passes when all keys are present")
    except ValueError as exc:
        _record_fail("U6 · validate_required_keys passes when all keys are present", str(exc))

    # ── Test U7: missing key raises ValueError with the key named ─────────
    def _check_missing():
        validate_required_keys({"category": "account"}, ["category", "priority"])

    assert_raises(
        "U7 · validate_required_keys raises ValueError listing missing key",
        ValueError,
        _check_missing,
    )

    # ── Test U8: extract_json full pipeline on fenced input ───────────────
    fenced = '```json\n{"category": "borrowing", "priority": "medium"}\n```'
    result = extract_json(fenced, required_keys=["category", "priority"])
    assert_equal(
        "U8 · extract_json returns correct dict from fenced JSON",
        result,
        {"category": "borrowing", "priority": "medium"},
    )

    # =========================================================================
    print_separator("UNIT TESTS — ClassificationService Input Validation")

    settings     = get_settings()
    ai_service   = ResilientAIService()
    usage_tracker = UsageTracker()
    rate_limiter  = TokenBucketRateLimiter()

    classifier = ClassificationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    # ── Test U9: empty string raises ValueError ────────────────────────────
    assert_raises(
        "U9  · empty ticket_text raises ValueError",
        ValueError,
        classifier.classify_ticket,
        "",
    )

    # ── Test U10: too-short text raises ValueError ─────────────────────────
    assert_raises(
        "U10 · ticket_text under 10 chars raises ValueError",
        ValueError,
        classifier.classify_ticket,
        "Hi",
    )

    # =========================================================================
    print_separator("UNIT TESTS — SummarisationService Input Validation")

    summariser = SummarisationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    # ── Test U11: empty list raises ValueError ─────────────────────────────
    assert_raises(
        "U11 · empty reviews list raises ValueError",
        ValueError,
        summariser.summarise_reviews,
        [],
    )

    # ── Test U12: list over 50 items raises ValueError ─────────────────────
    assert_raises(
        "U12 · list of 51 reviews raises ValueError",
        ValueError,
        summariser.summarise_reviews,
        ["review"] * 51,
    )

    # ── Test U13: non-string item in list raises ValueError ───────────────
    assert_raises(
        "U13 · non-string review item raises ValueError",
        ValueError,
        summariser.summarise_reviews,
        ["Great book", 42, "Another review"],
    )

    # ── Test U14: empty string in list raises ValueError ──────────────────
    assert_raises(
        "U14 · empty-string review item raises ValueError",
        ValueError,
        summariser.summarise_reviews,
        ["Great book", "   ", "Another review"],
    )


# =====================================================================
# ── LIVE INTEGRATION TESTS  (real AI calls) ──────────────────────────
# =====================================================================

def run_live_tests() -> None:
    """
    Run live end-to-end tests against a real AI provider.

    Requirements:
        - At least one API key configured in .env
        - Internet access

    These tests consume tokens and take several seconds each.
    """
    settings      = get_settings()
    ai_service    = ResilientAIService()
    usage_tracker = UsageTracker()
    rate_limiter  = TokenBucketRateLimiter()

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

    # ==================================================================
    # Ticket Classifier — Live Tests
    # ==================================================================
    print_separator("LIVE TESTS — ClassificationService  (real AI call)")

    # ── L1: frustrated account ticket ─────────────────────────────────
    ticket_frustrated = (
        "My library card isn't working at the self-checkout and "
        "I'm very frustrated. I've been trying for 20 minutes."
    )

    print(f"\n  [TICKET 1] {ticket_frustrated[:70]}...")
    result_1 = run_live_test(
        "L1 · classify_ticket (frustrated ticket)",
        classifier.classify_ticket,
        ticket_frustrated,
    )
    if result_1 is not None:
        print(f"  Result: {result_1}")
        assert_true(
            "L1 · classify_ticket returns a non-empty dict",
            isinstance(result_1, dict) and len(result_1) > 0,
            "Expected a non-empty dict."
        )

    # ── L2: low-priority suggestion ticket ────────────────────────────
    ticket_suggestion = (
        "It would be great if the library had a wider selection "
        "of audiobooks for learning languages."
    )

    print(f"\n  [TICKET 2] {ticket_suggestion[:70]}...")
    result_2 = run_live_test(
        "L2 · classify_ticket (suggestion ticket)",
        classifier.classify_ticket,
        ticket_suggestion,
    )
    if result_2 is not None:
        print(f"  Result: {result_2}")
        assert_true(
            "L2 · classify_ticket returns a non-empty dict for a suggestion",
            isinstance(result_2, dict) and len(result_2) > 0,
            "Expected a non-empty dict."
        )

    # ── L3–L6: field and enum checks only if L1 succeeded ────────────
    if result_1 is not None:
        # ── L3: all required output fields are present ────────────────
        required = ["category", "priority", "sentiment", "department", "summary"]
        for field in required:
            assert_true(
                f"L3 · output contains required field '{field}'",
                field in result_1,
                f"Field '{field}' missing from classification result."
            )

        # ── L4: category is within allowed values ─────────────────────
        assert_true(
            f"L4 · category value '{result_1.get('category')}' is in allowed set",
            result_1.get("category") in ALLOWED_CATEGORIES,
            f"Got {result_1.get('category')!r}, allowed: {sorted(ALLOWED_CATEGORIES)}"
        )

        # ── L5: priority is within allowed values ─────────────────────
        assert_true(
            f"L5 · priority value '{result_1.get('priority')}' is in allowed set",
            result_1.get("priority") in ALLOWED_PRIORITIES,
            f"Got {result_1.get('priority')!r}, allowed: {sorted(ALLOWED_PRIORITIES)}"
        )

        # ── L6: sentiment is within allowed values ────────────────────
        assert_true(
            f"L6 · sentiment value '{result_1.get('sentiment')}' is in allowed set",
            result_1.get("sentiment") in ALLOWED_SENTIMENTS,
            f"Got {result_1.get('sentiment')!r}, allowed: {sorted(ALLOWED_SENTIMENTS)}"
        )
    else:
        print("  [SKIP] L3–L6 skipped because L1 did not return a result.")

    # ==================================================================
    # Review Summariser — Live Tests
    # ==================================================================
    print_separator("LIVE TESTS — SummarisationService  (real AI call)")

    sample_reviews = [
        "This book completely pulled me in. The world-building is extraordinary "
        "and the characters feel real. 5 stars.",
        "I struggled through the first half. It picks up, but the slow start "
        "nearly made me give up. Rating: 3 out of 5.",
        "Absolutely loved it. Couldn't put it down once the plot kicked in. 5 stars.",
        "Decent read. Some parts were brilliant, others dragged on. 3.5 out of 5.",
        "The ending was satisfying but the middle section needed tighter editing. "
        "Still recommended for fans of the genre. 4/5.",
    ]

    print(f"\n  Submitting {len(sample_reviews)} reviews for summarisation...")
    summary = run_live_test(
        "L7 · summarise_reviews (5 mixed reviews)",
        summariser.summarise_reviews,
        sample_reviews,
    )
    if summary is not None:
        print(f"\n  Result:")
        import json as _json
        print("  " + _json.dumps(summary, indent=4).replace("\n", "\n  "))

    # ── L8–L10: content checks only if summariser call succeeded ──────
    if summary is not None:
        assert_true(
            "L7 · summarise_reviews returns a non-empty dict",
            isinstance(summary, dict) and len(summary) > 0,
            "Expected a non-empty dict."
        )

        # ── L8: all required output fields are present ────────────────
        required_summary = [
            "overall_sentiment", "average_rating", "key_themes",
            "praise", "criticism", "recommendation"
        ]
        for field in required_summary:
            assert_true(
                f"L8 · summary contains required field '{field}'",
                field in summary,
                f"Field '{field}' missing from summary result."
            )

        # ── L9: average_rating is a number ────────────────────────────
        rating = summary.get("average_rating")
        assert_true(
            f"L9 · average_rating is int or float (got {type(rating).__name__}: {rating})",
            isinstance(rating, (int, float)),
            f"Expected int or float, got {type(rating).__name__}: {rating!r}"
        )

        # ── L10: key_themes, praise, criticism are lists ──────────────
        for list_field in ("key_themes", "praise", "criticism"):
            value = summary.get(list_field)
            assert_true(
                f"L10 · '{list_field}' is a list (got {type(value).__name__})",
                isinstance(value, list),
                f"Expected list, got {type(value).__name__}: {value!r}"
            )
    else:
        print("  [SKIP] L7–L10 skipped because summarise_reviews did not return a result.")

    # ==================================================================
    # Usage Tracker — shared check
    # ==================================================================
    print_separator("LIVE TESTS — UsageTracker  (shared check)")

    total_requests = usage_tracker.get_total_requests()
    daily_cost     = usage_tracker.get_daily_cost()

    print(f"\n  Total AI requests recorded : {total_requests}")
    print(f"  Estimated cost this session: ${daily_cost:.6f} USD")

    # We made at least 2 live AI calls (2 classifier + 1 summariser = 3).
    assert_true(
        f"L11 · UsageTracker recorded at least 3 requests (got {total_requests})",
        total_requests >= 3,
        f"Expected >= 3 requests, got {total_requests}."
    )


# =====================================================================
# Main runner
# =====================================================================

def run_all_tests() -> None:
    """Run all unit tests then all live integration tests."""

    print("\n" + "█" * 64)
    print("  LibraryMind Part 6 — Classification & Summarisation Tests")
    print("█" * 64)

    # ── Phase 1: Unit tests ───────────────────────────────────────────
    print("\n\n📋  PHASE 1: Unit Tests  (no AI calls, offline-safe)")
    run_unit_tests()

    # ── Phase 2: Live integration tests ──────────────────────────────
    print("\n\n🌐  PHASE 2: Live Integration Tests  (real AI calls)")
    run_live_tests()

    # ── Final report ─────────────────────────────────────────────────
    total = _pass_count + _fail_count
    print("\n" + "=" * 64)
    print(f"  TEST RESULTS:  {_pass_count} passed,  {_fail_count} failed  (of {total} total)")
    print("=" * 64)

    if _fail_count == 0:
        print("\n  ✅  All tests passed. Part 6 is working correctly.")
    else:
        print(f"\n  ❌  {_fail_count} test(s) failed. Review the [FAIL] lines above.")

    print()


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as exc:
        logger.error(f"Test run aborted by unexpected exception: {exc}", exc_info=True)
        sys.exit(1)
