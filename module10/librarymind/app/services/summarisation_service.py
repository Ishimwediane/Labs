import logging
from typing import Any

from app.config import Settings
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.utils.json_output import extract_json
from app.api.models import BookReviewSentiment

logger = logging.getLogger(__name__)

MAX_REVIEWS = 50

REQUIRED_FIELDS = [
    "overall_sentiment",
    "average_rating",
    "key_themes",
    "praise",
    "criticism",
    "recommendation",
]

EXPECTED_TYPES: dict[str, type | tuple[type, ...]] = {
    "overall_sentiment": BookReviewSentiment,
    "average_rating":    (int, float),
    "key_themes":        list,
    "praise":            list,
    "criticism":         list,
    "recommendation":    str,
}


class SummarisationService:
    """Analyses a batch of book reviews and returns a structured JSON summary."""

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

    def summarise_reviews(self, reviews: list[str]) -> dict[str, Any]:
        """Summarise a list of book reviews into a structured analysis dict.

        Args:
            reviews: 1–50 non-empty review strings.

        Returns:
            Dict with keys: overall_sentiment, average_rating, key_themes,
            praise, criticism, recommendation.

        Raises:
            ValueError: If reviews are invalid or the model returns bad JSON.
            RuntimeError: If all AI providers fail.
        """
        reviews = self._validate_reviews(reviews)
        logger.info(f"Summarising {len(reviews)} review(s).")

        self.rate_limiter.acquire()

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(reviews)

        raw_response = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.0,
            max_tokens=800,
        )
        logger.debug(f"Raw model response:\n{raw_response}")

        summary = extract_json(raw_text=raw_response, required_keys=REQUIRED_FIELDS)
        
        # Normalize and validate overall_sentiment enum
        sentiment_str = str(summary.get("overall_sentiment", "")).strip().lower()
        matched_enum = None
        for item in BookReviewSentiment:
            if item.value == sentiment_str:
                matched_enum = item
                break
        if not matched_enum:
            raise ValueError(
                f"Invalid 'overall_sentiment': {summary.get('overall_sentiment')!r}. "
                f"Allowed: {sorted([e.value for e in BookReviewSentiment])}."
            )
        summary["overall_sentiment"] = matched_enum

        self._validate_field_types(summary)
        self._record_usage(prompt=system_prompt + user_prompt, completion=raw_response)

        logger.info(
            f"Summarisation complete. Sentiment: {summary.get('overall_sentiment')}, "
            f"Rating: {summary.get('average_rating')}, "
            f"Themes: {len(summary.get('key_themes', []))}"
        )
        return summary

    def _validate_reviews(self, reviews: list[str]) -> list[str]:
        """Validate input list and return stripped reviews; raise ValueError on bad input."""
        if not isinstance(reviews, list):
            raise ValueError(f"reviews must be a list, got {type(reviews).__name__}.")
        if len(reviews) == 0:
            raise ValueError("reviews list must not be empty.")
        if len(reviews) > MAX_REVIEWS:
            raise ValueError(f"Too many reviews. Max {MAX_REVIEWS}, got {len(reviews)}.")

        cleaned: list[str] = []
        for i, item in enumerate(reviews):
            if not isinstance(item, str):
                raise ValueError(
                    f"Review at index {i} must be a string, got {type(item).__name__}."
                )
            stripped = item.strip()
            if not stripped:
                raise ValueError(f"Review at index {i} is empty after stripping.")
            cleaned.append(stripped)
        return cleaned

    def _build_system_prompt(self) -> str:
        return (
            "You are a book review analysis engine for a library system.\n"
            "\n"
            "STRICT RULES:\n"
            "  1. Return ONLY a single valid JSON object. No markdown. No explanation.\n"
            "  2. Do not wrap the JSON in code fences.\n"
            "  3. Do not add any text before or after the JSON.\n"
            "  4. Analyse ALL reviews together holistically, not individually.\n"
            "  5. Keep values SHORT: list items max 8 words, lists max 5 items, "
            "recommendation max 15 words.\n"
            "  6. Output the JSON on a SINGLE LINE with no newlines inside it.\n"
            "\n"
            "Required JSON fields:\n"
            "  - overall_sentiment  (string)       – 'positive', 'negative', or 'mixed'\n"
            "  - average_rating     (number)       – estimated average out of 5.0\n"
            "  - key_themes         (list[string]) – max 5 themes across reviews\n"
            "  - praise             (list[string]) – max 5 things readers liked\n"
            "  - criticism          (list[string]) – max 5 things readers disliked\n"
            "  - recommendation     (string)       – one-sentence recommendation, max 15 words\n"
            "\n"
            "If reviews mention no ratings, estimate from sentiment.\n"
        )

    def _build_user_prompt(self, reviews: list[str]) -> str:
        numbered = "\n".join(f"[{i + 1}] {review}" for i, review in enumerate(reviews))
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
        """Check each required field has the expected Python type."""
        for field, expected_type in EXPECTED_TYPES.items():
            value = data[field]
            if not isinstance(value, expected_type):
                type_name = (
                    " or ".join(t.__name__ for t in expected_type)
                    if isinstance(expected_type, tuple)
                    else expected_type.__name__
                )
                raise ValueError(
                    f"Field '{field}' has wrong type. "
                    f"Expected {type_name}, got {type(value).__name__} ({value!r})."
                )
        logger.debug("All field types validated successfully.")

    def _record_usage(self, prompt: str, completion: str) -> None:
        """Record token usage and estimated cost for the active provider."""
        provider = self.settings.PRIMARY_PROVIDER
        model_map = {
            "openai":    self.settings.OPENAI_MODEL,
            "anthropic": self.settings.ANTHROPIC_MODEL,
            "gemini":    self.settings.GEMINI_MODEL,
            "amalitech": self.settings.OPENAI_MODEL,
        }
        self.usage_tracker.record_usage(
            provider=provider,
            model=model_map.get(provider, self.settings.OPENAI_MODEL),
            prompt=prompt,
            completion=completion,
        )
