"""
app/utils/json_output.py
=========================
Part 6 — Shared JSON Output Utilities

WHAT THIS FILE DOES:
    Provides three small helper functions that BOTH Part 6 services use
    to turn a raw AI model response into a clean, validated Python dict.

    The pipeline is always the same three steps:

        raw model text
              │
              ▼
        strip_markdown_fences()   ← removes ```json … ``` wrappers
              │
              ▼
        parse_json_safely()       ← converts string to Python dict
              │
              ▼
        validate_required_keys()  ← checks all expected fields exist
              │
              ▼
        clean dict  ✅   OR   ValueError raised  ❌

WHY THIS IS A SEPARATE FILE:
    ClassificationService and SummarisationService both need the same
    three steps. Putting them here avoids copy-pasting the same logic
    in two places. If the parsing logic ever needs to change, you only
    change it once.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ======================================================================
# Step 1 — Markdown Fence Stripper
# ======================================================================

def strip_markdown_fences(raw_text: str) -> str:
    """
    Remove markdown code fences that AI models sometimes wrap around JSON.

    Even when a prompt says "return JSON only", models occasionally reply
    with:

        ```json
        { "key": "value" }
        ```

    or just:

        ```
        { "key": "value" }
        ```

    This function strips those wrappers so the next step (json.loads)
    receives a clean JSON string.

    Args:
        raw_text: The unmodified string returned by the AI model.

    Returns:
        A string with any leading/trailing code fences removed.
        If no fences are present, the original string is returned unchanged.

    Examples:
        >>> strip_markdown_fences('```json\\n{"a": 1}\\n```')
        '{"a": 1}'

        >>> strip_markdown_fences('{"a": 1}')
        '{"a": 1}'
    """
    # Strip leading/trailing whitespace first.
    text = raw_text.strip()

    # Pattern: optional "json" or other language tag after the opening ```.
    # re.DOTALL lets . match newlines inside the fence.
    fence_pattern = re.compile(r"^```(?:json|python|text)?\s*(.*?)\s*```$", re.DOTALL)
    match = fence_pattern.match(text)

    if match:
        # Fences found — return only the content inside them.
        cleaned = match.group(1).strip()
        logger.debug("Markdown code fences stripped from model output.")
        return cleaned

    # No fences — return as-is.
    return text


# ======================================================================
# Step 2 — JSON Parser
# ======================================================================

def parse_json_safely(text: str) -> dict[str, Any]:
    """
    Parse a JSON string into a Python dictionary.

    This is a thin wrapper around json.loads() that raises a clear,
    descriptive ValueError instead of the default JSONDecodeError,
    so the calling service can produce a meaningful error message.

    Args:
        text: A string that should contain valid JSON.

    Returns:
        A Python dict parsed from the JSON string.

    Raises:
        ValueError: If the string cannot be parsed as JSON.
                    The error message includes the first 200 characters
                    of the bad input so the developer can see what went wrong.

    Example:
        >>> parse_json_safely('{"category": "account"}')
        {'category': 'account'}

        >>> parse_json_safely("This is not JSON")
        ValueError: Model returned invalid JSON. ...
    """
    try:
        parsed = json.loads(text)
        logger.debug("JSON parsed successfully.")
        return parsed
    except json.JSONDecodeError as exc:
        # Truncate the bad input in the error message for readability.
        preview = text[:200].replace("\n", " ")
        raise ValueError(
            f"Model returned invalid JSON and could not be parsed.\n"
            f"Parse error: {exc}\n"
            f"Raw output preview: {preview!r}"
        ) from exc


# ======================================================================
# Step 3 — Required-Field Validator
# ======================================================================

def validate_required_keys(data: dict[str, Any], required_keys: list[str]) -> None:
    """
    Check that a parsed JSON dict contains all expected fields.

    This step ensures that even if the model produces valid JSON, it has
    not silently omitted any field that downstream code depends on.

    Args:
        data:          A Python dict (output of parse_json_safely).
        required_keys: A list of field names that must be present.

    Returns:
        None. The function is silent on success.

    Raises:
        ValueError: If one or more required keys are missing.
                    The error message lists exactly which keys are missing.

    Example:
        >>> validate_required_keys({"a": 1}, ["a", "b"])
        ValueError: Model output is missing required fields: ['b']. ...
    """
    missing = [key for key in required_keys if key not in data]

    if missing:
        raise ValueError(
            f"Model output is missing required fields: {missing}.\n"
            f"Expected fields: {required_keys}.\n"
            f"Received fields: {list(data.keys())}."
        )

    logger.debug(f"All required fields present: {required_keys}")


# ======================================================================
# Convenience Pipeline
# ======================================================================

def extract_json(raw_text: str, required_keys: list[str]) -> dict[str, Any]:
    """
    Run all three steps of the JSON extraction pipeline in one call.

    This is the main function both services use. It:
        1. Strips markdown code fences.
        2. Parses the JSON string.
        3. Validates that required fields are present.

    Args:
        raw_text:      The unmodified string returned by the AI model.
        required_keys: List of fields that must exist in the parsed dict.

    Returns:
        A validated Python dict.

    Raises:
        ValueError: If any step fails (invalid JSON or missing fields).

    Example usage in a service:
        result = extract_json(
            raw_text=model_response,
            required_keys=["category", "priority", "sentiment"]
        )
    """
    # ── Step 1: Strip markdown code fences ────────────────────────────
    clean_text = strip_markdown_fences(raw_text)

    # ── Step 2: Parse JSON ─────────────────────────────────────────────
    data = parse_json_safely(clean_text)

    # ── Step 3: Validate required fields ──────────────────────────────
    validate_required_keys(data, required_keys)

    return data
