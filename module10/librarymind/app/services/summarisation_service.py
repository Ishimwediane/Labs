"""

WHAT THIS FILE DOES:
    SummarisationService takes a list of 1–50 book review strings and
    returns a structured JSON dict describing:

        {
            "overall_sentiment": "positive",
            "average_rating":    4.2,
            "key_themes":        ["engaging plot", "clear writing"],
            "praise":            ["Strong character development", "..."],
            "criticism":         ["Slow opening chapter"],
            "recommendation":    "Recommended for fans of historical fiction."
        }

HOW IT WORKS (step by step):
    1.  Receive a list of review strings.
    2.  Validate the list (not empty, max 50, each item non-empty string).
    3.  Check the rate limiter (raises error if too many requests).
    4.  Build a prompt asking for holistic analysis (not one-by-one) as JSON.
    5.  Send the prompt through ResilientAIService at low temperature.
    6.  Receive the raw model response (may contain markdown fences).
    7.  Strip markdown fences if present.       ← json_output.py Step 1
    8.  Parse the JSON string to a Python dict. ← json_output.py Step 2
    9.  Validate that all required fields exist. ← json_output.py Step 3
    10. Validate that each field has the correct Python type.
    11. Record token usage and estimated cost.
    12. Return the clean summary dict.
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


# Constants


# Maximum number of reviews allowed in one request.
MAX_REVIEWS = 50

# Fields that must be present in every summarisation response.
REQUIRED_FIELDS = [
    "overall_sentiment",
    "average_rating",
    "key_themes",
    "praise",
    "criticism",
    "recommendation",
]

# Expected Python types for each field.
# Used to validate that the model returned sensible data.
EXPECTED_TYPES: dict[str, type | tuple[type, ...]] = {
    "overall_sentiment": str,
    "average_rating":    (int, float),
    "key_themes":        list,
    "praise":            list,
    "criticism":         list,
    "recommendation":    str,
}


# SummarisationService


class SummarisationService:
    """
    Summarises a collection of book reviews into a structured JSON response.

    Responsibilities:
    - Input validation (list type, length, each item non-empty string).
    - Prompt construction (holistic analysis, JSON-only output).
    - AI generation via ResilientAIService.
    - JSON extraction and field validation via the shared json_output pipeline.
    - Type validation for each output field.
    - Usage recording via UsageTracker.

    Usage:
        service = SummarisationService(
            ai_service=ai_service,
            usage_tracker=usage_tracker,
            rate_limiter=rate_limiter,
            settings=settings,
        )
        result = service.summarise_reviews([
            "Loved the characters, the plot felt slow.",
            "A masterpiece. Could not put it down.",
            ...
        ])
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

        logger.info("SummarisationService initialised.")

    # PUBLIC METHOD


    def summarise_reviews(self, reviews: list[str]) -> dict[str, Any]:
        """
        Analyse a list of reviews and return a structured summary dict.

        The model is asked to look across ALL reviews holistically, not
        one by one, to produce a high-level synthesis.

        Args:
            reviews: A list of 1–50 non-empty review strings.

        Returns:
            A dict with the following guaranteed keys:
                "overall_sentiment" – string  (e.g. "positive")
                "average_rating"    – int or float  (e.g. 4.2)
                "key_themes"        – list of strings
                "praise"            – list of strings (what readers liked)
                "criticism"         – list of strings (what readers disliked)
                "recommendation"    – string (one-sentence recommendation)

        Raises:
            ValueError:   If reviews are invalid, or the model returns
                          invalid / incomplete / wrongly-typed JSON.
            RuntimeError: If all AI providers fail (from ResilientAIService).
        """
        # 1: Validate input 
        reviews = self._validate_reviews(reviews)

        logger.info(f"Summarising {len(reviews)} review(s).")

        # 2: Check rate limiter     
        # Raises RateLimitExceededError (HTTP 429) if the bucket is empty.
        self.rate_limiter.acquire()

        #3: Build prompts 
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(reviews)

        # 4: Call the AI provider 
    
        raw_response = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.0,
            max_tokens=800,   # Generous budget — lists inside JSON must not be truncated.
        )

        logger.debug(f"Raw model response:\n{raw_response}")

        # 5–7: Strip fences → parse JSON → validate fields
    
        summary = extract_json(
            raw_text=raw_response,
            required_keys=REQUIRED_FIELDS,
        )

        # 8: Validate field types
        self._validate_field_types(summary)

        # 9: Record token usage and cost
        self._record_usage(
            prompt=system_prompt + user_prompt,
            completion=raw_response,
        )

        logger.info(
            f"Summarisation complete. "
            f"Sentiment: {summary.get('overall_sentiment')}, "
            f"Rating: {summary.get('average_rating')}, "
            f"Themes: {len(summary.get('key_themes', []))}"
        )

        return summary

    # PRIVATE HELPERS


    def _validate_reviews(self, reviews: list[str]) -> list[str]:
        """
        Ensure the input is a valid non-empty list of strings.

        Validation rules:
            - Must be a Python list.
            - Must contain at least 1 and at most MAX_REVIEWS (50) items.
            - Each item must be a non-empty string after stripping whitespace.

        Args:
            reviews: Raw input from the caller.

        Returns:
            A new list with each review stripped of leading/trailing whitespace.

        Raises:
            ValueError: If any validation rule is broken.
        """
        if not isinstance(reviews, list):
            raise ValueError(
                f"reviews must be a list, got {type(reviews).__name__}."
            )

        if len(reviews) == 0:
            raise ValueError("reviews list must not be empty.")

        if len(reviews) > MAX_REVIEWS:
            raise ValueError(
                f"Too many reviews. Maximum allowed is {MAX_REVIEWS}, "
                f"but {len(reviews)} were provided."
            )

        cleaned: list[str] = []
        for i, item in enumerate(reviews):
            if not isinstance(item, str):
                raise ValueError(
                    f"Review at index {i} must be a string, "
                    f"got {type(item).__name__}."
                )
            stripped = item.strip()
            if not stripped:
                raise ValueError(
                    f"Review at index {i} is empty after stripping whitespace."
                )
            cleaned.append(stripped)

        return cleaned

    def _build_system_prompt(self) -> str:
        """
        Build the system-level instruction for the model.

        The prompt enforces:
        - A holistic, cross-review analysis (not a one-by-one summary).
        - JSON-only output with no extra text.
        - The exact field names and their expected types.

        Returns:
            A multi-line instruction string for the 'system' argument.
        """
        return (
            "You are a book review analysis engine for a library system.\n"
            "\n"
            "STRICT RULES:\n"
            "  1. Return ONLY a single valid JSON object. No markdown. No explanation.\n"
            "  2. Do not wrap the JSON in code fences (no ``` markers).\n"
            "  3. Do not add any text before or after the JSON.\n"
            "  4. Analyse ALL reviews together holistically. "
            "Do not summarise each review individually.\n"
            "  5. Keep ALL string values SHORT. Each list item: max 8 words. "
            "Each list: max 5 items. The recommendation string: max 15 words.\n"
            "  6. Output the JSON on a SINGLE LINE with no newlines inside it.\n"
            "\n"
            "Required JSON fields:\n"
            "  - overall_sentiment  (string)       – 'positive', 'negative', or 'mixed'\n"
            "  - average_rating     (number)       – estimated average score out of 5.0\n"
            "  - key_themes         (list[string]) – max 5 short themes across reviews\n"
            "  - praise             (list[string]) – max 5 things readers consistently liked\n"
            "  - criticism          (list[string]) – max 5 things readers consistently disliked\n"
            "  - recommendation     (string)       – max 15 words, one-sentence recommendation\n"
            "\n"
            "If reviews mention no ratings, estimate based on sentiment.\n"
        )

    def _build_user_prompt(self, reviews: list[str]) -> str:
        """
        Build the user-side prompt containing all reviews.

        Each review is numbered and separated for readability.

        Args:
            reviews: The validated, stripped list of review strings.

        Returns:
            A prompt string ready to be sent to the AI model.
        """
        numbered = "\n".join(
            f"[{i + 1}] {review}" for i, review in enumerate(reviews)
        )

        return (
            f"Analyse the following {len(reviews)} book review(s) as a whole.\n"
            "Return ONLY a JSON object with fields: "
            "overall_sentiment, average_rating, key_themes, praise, criticism, recommendation.\n"
            "\n"
            f"REVIEWS:\n{numbered}\n"
            "\n"
            "JSON:"
        )

    def _validate_field_types(self, data: dict[str, Any]) -> None:
        """
        Verify that each required field has the correct Python type.

        This catches cases where the model returns a field with the right
        name but the wrong type (e.g. average_rating as a string "4.2").

        Args:
            data: The parsed and field-validated summary dict.

        Raises:
            ValueError: If any field has an unexpected type.
        """
        for field, expected_type in EXPECTED_TYPES.items():
            value = data[field]
            if not isinstance(value, expected_type):
                # Make the type expectation human-readable in the error.
                if isinstance(expected_type, tuple):
                    type_name = " or ".join(t.__name__ for t in expected_type)
                else:
                    type_name = expected_type.__name__

                raise ValueError(
                    f"Field '{field}' has wrong type. "
                    f"Expected {type_name}, got {type(value).__name__} "
                    f"with value {value!r}."
                )

        logger.debug("All field types validated successfully.")

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

# QUICK DEMO  (run with: python -m app.services.summarisation_service)


if __name__ == "__main__":
    """
    Minimal wiring to demonstrate how to use SummarisationService.
    No web server required — just run this file directly.

    To run:
        cd librarymind
        python -m app.services.summarisation_service
    """
    import json
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    from app.config import get_settings
    from app.infrastructure.rate_limiter import TokenBucketRateLimiter
    from app.infrastructure.usage_tracker import UsageTracker
    from app.providers.resilient_service import ResilientAIService

    settings      = get_settings()
    ai_service    = ResilientAIService()
    usage_tracker = UsageTracker()
    rate_limiter  = TokenBucketRateLimiter()

    # Instantiate the service 
    summariser = SummarisationService(
        ai_service=ai_service,
        usage_tracker=usage_tracker,
        rate_limiter=rate_limiter,
        settings=settings,
    )

    # Example reviews 
    sample_reviews = [
        "This book completely pulled me in. The world-building is extraordinary "
        "and the characters feel real. A must-read for sci-fi fans.",
        "I struggled through the first half. It picks up, but the slow start "
        "nearly made me give up. Rating: 3/5.",
        "Absolutely loved it. Couldn't put it down once the plot kicked in. 5 stars.",
        "Decent read. Some parts were brilliant, others dragged on. 3.5 out of 5.",
        "The ending was satisfying but the middle section needed tighter editing. "
        "Still recommended for fans of the genre.",
    ]

    print("\n" + "=" * 60)
    print(f"INPUT: {len(sample_reviews)} reviews")
    print("=" * 60)
    for i, r in enumerate(sample_reviews, 1):
        print(f"[{i}] {r[:80]}...")

    result = summariser.summarise_reviews(sample_reviews)

    print("\n" + "=" * 60)
    print("SUMMARY RESULT:")
    print("=" * 60)
    print(json.dumps(result, indent=2))

    print(f"\nTotal requests tracked: {usage_tracker.get_total_requests()}")
    print(f"Estimated cost so far:  ${usage_tracker.get_daily_cost():.6f} USD")
