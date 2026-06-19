import logging
from typing import Any

from app.config import Settings
from app.infrastructure.rate_limiter import TokenBucketRateLimiter
from app.infrastructure.usage_tracker import UsageTracker
from app.providers.resilient_service import ResilientAIService
from app.utils.json_output import extract_json
from app.api.models import LibraryDepartment

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = {"account", "borrowing", "technical", "complaint", "suggestion", "general"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
ALLOWED_SENTIMENTS = {"positive", "neutral", "negative"}
REQUIRED_FIELDS = ["category", "priority", "sentiment", "department", "summary"]




class ClassificationService:
    """Classifies raw support tickets into structured JSON using an AI model."""

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

    def classify_ticket(self, ticket_text: str) -> dict[str, Any]:
        """Classify a support ticket and return a validated structured dict.

        Args:
            ticket_text: Raw ticket text from a patron or staff member.

        Returns:
            Dict with keys: category, priority, sentiment, department, summary.

        Raises:
            ValueError: If ticket_text is invalid or the model returns bad JSON.
            RuntimeError: If all AI providers fail.
        """
        ticket_text = self._validate_ticket_text(ticket_text)
        logger.info(f"Classifying ticket: '{ticket_text[:60]}...'")

        self.rate_limiter.acquire()

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(ticket_text)

        raw_response = self.ai_service.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.0,
            max_tokens=600,
        )
        logger.debug(f"Raw model response:\n{raw_response}")

        classification = extract_json(raw_text=raw_response, required_keys=REQUIRED_FIELDS)
        self._validate_enum_fields(classification)
        self._record_usage(prompt=system_prompt + user_prompt, completion=raw_response)

        logger.info(
            f"Classified: category={classification['category']}, "
            f"priority={classification['priority']}, "
            f"sentiment={classification['sentiment']}"
        )
        return classification

    def _validate_ticket_text(self, ticket_text: str) -> str:
        """Validate and strip ticket text; raise ValueError if too short."""
        if not isinstance(ticket_text, str):
            raise ValueError(f"ticket_text must be a string, got {type(ticket_text).__name__}.")
        ticket_text = ticket_text.strip()
        if len(ticket_text) < 10:
            raise ValueError("ticket_text is too short. Provide at least 10 characters.")
        return ticket_text

    def _build_system_prompt(self) -> str:
        return (
            "You are a ticket classification engine for a library support system.\n"
            "\n"
            "STRICT RULES:\n"
            "  1. Return ONLY a single valid JSON object. No markdown. No explanation.\n"
            "  2. Do not wrap the JSON in code fences.\n"
            "  3. Do not add any text before or after the JSON.\n"
            "  4. Keep ALL string values SHORT to avoid truncation.\n"
            "  5. Output the JSON on a SINGLE LINE with no newlines inside it.\n"
            "\n"
            "Required JSON fields and allowed values:\n"
            "  - category:   one of: account, borrowing, technical, complaint, suggestion, general\n"
            "  - priority:   one of: low, medium, high, urgent\n"
            "  - sentiment:  one of: positive, neutral, negative\n"
            "  - department: one of: Circulation, IT Support, Collections, Reference, Membership, Billing, Administration\n"
            "  - summary:    max 12 words describing the issue\n"
            "\n"
            "Priority guidance:\n"
            "  - urgent: service outages or access emergencies\n"
            "  - high:   patron frustration or inability to use a service\n"
            "  - medium: general problems that can wait\n"
            "  - low:    suggestions or non-urgent questions\n"
        )

    def _build_user_prompt(self, ticket_text: str) -> str:
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
        """Validate and normalise category, priority, and sentiment to lowercase; department to canonical title case."""
        checks = [
            ("category",  data["category"],  ALLOWED_CATEGORIES),
            ("priority",  data["priority"],  ALLOWED_PRIORITIES),
            ("sentiment", data["sentiment"], ALLOWED_SENTIMENTS),
        ]
        for field_name, value, allowed_set in checks:
            if str(value).lower() not in allowed_set:
                raise ValueError(
                    f"Invalid '{field_name}': {value!r}. Allowed: {sorted(allowed_set)}."
                )
            data[field_name] = str(value).lower()

        dept_str = str(data.get("department", "")).strip().lower()
        matched_enum = None
        for item in LibraryDepartment:
            if item.value.lower() == dept_str:
                matched_enum = item
                break

        if not matched_enum:
            allowed_vals = [e.value for e in LibraryDepartment]
            raise ValueError(
                f"Invalid 'department': {data.get('department')!r}. Allowed: {sorted(allowed_vals)}."
            )
        data["department"] = matched_enum

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
