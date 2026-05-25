"""
app/services/classification_service.py
=======================================
Part 6 — Ticket Classification Service

WHAT THIS FILE DOES:
    ClassificationService takes a raw support ticket (plain text) and
    returns a structured JSON dict describing:

        {
            "category":   "account",
            "priority":   "high",
            "sentiment":  "frustrated",
            "department": "membership",
            "summary":    "Patron cannot access account due to locked card."
        }

HOW IT WORKS (step by step):
    1.  Receive the raw ticket text.
    2.  Validate that the text is not empty or too short.
    3.  Check the rate limiter (raises error if too many requests).
    4.  Build a strict prompt that tells the model: "return JSON only".
    5.  Send the prompt through ResilientAIService at low temperature.
    6.  Receive the raw model response (may contain markdown fences).
    7.  Strip markdown fences if present.       ← json_output.py Step 1
    8.  Parse the JSON string to a Python dict. ← json_output.py Step 2
    9.  Validate that all required fields exist. ← json_output.py Step 3
    10. Validate that enum fields contain allowed values.
    11. Record token usage and estimated cost.
    12. Return the clean classification dict.
        OR raise a clear error if any step fails.

DEPENDENCIES (all from earlier parts):
    - ResilientAIService  → sends prompt to OpenAI / Claude / Gemini
    - UsageTracker        → records tokens and cost
    - TokenBucketRateLimiter → prevents request flooding
    - Settings            → API keys, model names, config
    - extract_json()      → shared parsing pipeline (app/utils/json_output.py)
"""

import logging
from typing import Any

from app.config import Settings
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.utils.json_output import extract_json

logger = logging.getLogger(__name__)


# ======================================================================
# Allowed values for enum-like fields
# ======================================================================

ALLOWED_CATEGORIES = {"account", "borrowing", "technical", "complaint", "suggestion", "general"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
ALLOWED_SENTIMENTS = {"positive", "neutral", "negative"}

# Fields that must be present in every classification response.
REQUIRED_FIELDS = ["category", "priority", "sentiment", "department", "summary"]


# ======================================================================
# ClassificationService
# ======================================================================

class ClassificationService:
    """
    Classifies a raw support ticket into a structured JSON response.

    Responsibilities:
    - Input validation (empty check, length check).
    - Prompt construction (strict JSON-only instruction).
    - AI generation via ResilientAIService.
    - JSON extraction and field validation via the shared json_output pipeline.
    - Enum value validation (category, priority, sentiment).
    - Usage recording via UsageTracker.

    Usage:
        service = ClassificationService(
            ai_service=ai_service,
            usage_tracker=usage_tracker,
            rate_limiter=rate_limiter,
            settings=settings,
        )
        result = service.classify_ticket("My card is locked and I can't log in.")
    """

    def __init__(
        self,
        ai_service: ResilientAIService,
        usage_tracker: UsageTracker,
        rate_limiter: TokenBucketRateLimiter,
        settings: Settings,
    ) -> None:
        self.ai_service = ai_service
        self.usage_tracker = usage_tracker
        self.rate_limiter = rate_limiter
        self.settings = settings

        logger.info("ClassificationService initialised.")

    # ==================================================================
    # PUBLIC METHOD
    # ==================================================================

    def classify_ticket(self, ticket_text: str) -> dict[str, Any]:
        """
        Classify a raw support ticket and return a structured dict.

        Args:
            ticket_text: The raw text of the support ticket submitted
                         by a patron or staff member.

        Returns:
            A dict with the following guaranteed keys:
                "category"   – one of: account, borrowing, technical,
                                        complaint, suggestion, general
                "priority"   – one of: low, medium, high, urgent
                "sentiment"  – one of: positive, neutral, negative
                "department" – the department best suited to handle it
                "summary"    – one-sentence summary of the ticket

        Raises:
            ValueError:   If ticket_text is empty, too short, or the model
                          returns invalid / incomplete JSON.
            RuntimeError: If all AI providers fail (from ResilientAIService).
        """
        # ── Step 1: Validate input ─────────────────────────────────────
        ticket_text = self._validate_ticket_text(ticket_text)

        logger.info(f"Classifying ticket. Preview: '{ticket_text[:60]}...'")

        # ── Step 2: Check rate limiter ─────────────────────────────────
        # Raises RateLimitExceededError (HTTP 429) if the bucket is empty.
        self.rate_limiter.acquire()

        # ── Step 3: Build prompts ──────────────────────────────────────
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(ticket_text)

        # ── Step 4: Call the AI provider ───────────────────────────────
        # temperature=0.0 → most deterministic output, best for JSON tasks.
        raw_response = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.0,
            max_tokens=600,   # Generous budget — JSON must not be truncated mid-string.
        )

        logger.debug(f"Raw model response:\n{raw_response}")

        # ── Steps 5–7: Strip fences → parse JSON → validate fields ─────
        # extract_json() runs all three steps from app/utils/json_output.py
        # and raises a clear ValueError if any step fails.
        classification = extract_json(
            raw_text=raw_response,
            required_keys=REQUIRED_FIELDS,
        )

        # ── Step 8: Validate enum values ───────────────────────────────
        self._validate_enum_fields(classification)

        # ── Step 9: Record token usage and cost ────────────────────────
        self._record_usage(
            prompt=system_prompt + user_prompt,
            completion=raw_response,
        )

        logger.info(
            f"Ticket classified: category={classification['category']}, "
            f"priority={classification['priority']}, "
            f"sentiment={classification['sentiment']}"
        )

        return classification

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================

    def _validate_ticket_text(self, ticket_text: str) -> str:
        """
        Ensure the ticket text is a non-empty string of reasonable length.

        Args:
            ticket_text: Raw input from the caller.

        Returns:
            Stripped version of the text.

        Raises:
            ValueError: If the text is empty or under 10 characters.
        """
        if not isinstance(ticket_text, str):
            raise ValueError(
                f"ticket_text must be a string, got {type(ticket_text).__name__}."
            )

        ticket_text = ticket_text.strip()

        if len(ticket_text) < 10:
            raise ValueError(
                "ticket_text is too short. Please provide at least 10 characters."
            )

        return ticket_text

    def _build_system_prompt(self) -> str:
        """
        Build the system-level instruction that tells the model what to do.

        The system prompt enforces:
        - The JSON-only output rule.
        - The exact field names and allowed enum values.
        - A prohibition on adding any extra text.

        Returns:
            A multi-line instruction string for the 'system' argument.
        """
        return (
            "You are a ticket classification engine for a library support system.\n"
            "\n"
            "STRICT RULES:\n"
            "  1. Return ONLY a single valid JSON object. No markdown. No explanation.\n"
            "  2. Do not wrap the JSON in code fences (no ``` markers).\n"
            "  3. Do not add any text before or after the JSON.\n"
            "  4. Keep ALL string values SHORT to avoid truncation.\n"
            "  5. Output the JSON on a SINGLE LINE with no newlines inside it.\n"
            "\n"
            "Required JSON fields and allowed values:\n"
            "  - category:   one of: account, borrowing, technical, complaint, suggestion, general\n"
            "  - priority:   one of: low, medium, high, urgent\n"
            "  - sentiment:  one of: positive, neutral, negative\n"
            "  - department: 1-3 words (e.g. 'Membership', 'IT Support', 'Collections')\n"
            "  - summary:    max 12 words describing the issue\n"
            "\n"
            "Guidance:\n"
            "  - priority 'urgent' is for service outages or access emergencies.\n"
            "  - priority 'high' is for clear patron frustration or inability to use a service.\n"
            "  - priority 'medium' is for general problems that can wait.\n"
            "  - priority 'low' is for suggestions or non-urgent questions.\n"
        )

    def _build_user_prompt(self, ticket_text: str) -> str:
        """
        Build the user-side prompt containing the ticket to classify.

        Args:
            ticket_text: The validated, stripped ticket text.

        Returns:
            A prompt string ready to be sent to the AI model.
        """
        return (
            "Classify the following support ticket.\n"
            "Return ONLY a JSON object with fields: "
            "category, priority, sentiment, department, summary.\n"
            "\n"
            f"TICKET:\n{ticket_text}\n"
            "\n"
            "JSON:"
        )

    def _validate_enum_fields(self, data: dict[str, Any]) -> None:
        """
        Check that category, priority, and sentiment contain allowed values.

        Args:
            data: The parsed classification dict (already field-validated).

        Raises:
            ValueError: If any enum field contains an unexpected value.
        """
        checks = [
            ("category",  data["category"],  ALLOWED_CATEGORIES),
            ("priority",  data["priority"],  ALLOWED_PRIORITIES),
            ("sentiment", data["sentiment"], ALLOWED_SENTIMENTS),
        ]

        for field_name, value, allowed_set in checks:
            if str(value).lower() not in allowed_set:
                raise ValueError(
                    f"Invalid value for '{field_name}': {value!r}.\n"
                    f"Allowed values: {sorted(allowed_set)}."
                )

            # Normalise to lowercase so callers get consistent output.
            data[field_name] = str(value).lower()

    def _record_usage(self, prompt: str, completion: str) -> None:
        """
        Record token usage and estimated cost via UsageTracker.

        UsageTracker.record_usage() signature:
            record_usage(provider: str, model: str, prompt: str, completion: str)
                → returns a usage dict (we don't need the return value here)

        Args:
            prompt:     The full prompt string sent to the model.
            completion: The raw string received back from the model.
        """
        provider = self.settings.PRIMARY_PROVIDER

        # Pick the correct model name based on the primary provider.
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        model = model_map.get(provider, self.settings.OPENAI_MODEL)

        self.usage_tracker.record_usage(
            provider=provider,
            model=model,
            prompt=prompt,
            completion=completion,
        )


# ======================================================================
# QUICK DEMO  (run with: python -m app.services.classification_service)
# ======================================================================

if __name__ == "__main__":
    """
    Minimal wiring to demonstrate how to use ClassificationService.
    No web server required — just run this file directly.

    To run:
        cd librarymind
        python -m app.services.classification_service
    """
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    from app.config import get_settings
    from app.infrastructure.rate_limiter import TokenBucketRateLimiter
    from app.infrastructure.usage_tracker import UsageTracker
    from app.providers.resilient_service import ResilientAIService

    settings     = get_settings()
    ai_service   = ResilientAIService()
    usage_tracker = UsageTracker()
    rate_limiter  = TokenBucketRateLimiter()

    # ── Instantiate the service ────────────────────────────────────────
    classifier = ClassificationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    # ── Example call ───────────────────────────────────────────────────
    ticket = (
        "My library card isn't working at the self-checkout and "
        "I'm very frustrated. I've been trying for 20 minutes."
    )

    print("\n" + "=" * 60)
    print("INPUT TICKET:")
    print(ticket)
    print("=" * 60)

    result = classifier.classify_ticket(ticket)

    print("\nCLASSIFICATION RESULT:")
    import json
    print(json.dumps(result, indent=2))

    print(f"\nTotal requests tracked: {usage_tracker.get_total_requests()}")
    print(f"Estimated cost so far:  ${usage_tracker.get_daily_cost():.6f} USD")
