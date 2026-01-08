import logging
import re
from typing import Any, Dict

from src.pipeline.exceptions import AnalysisError, CleaningError, StorageError

logger = logging.getLogger(__name__)


class TextCleaner:
    """Cleans raw text input."""

    def process(self, text: str) -> str:
        if text is None:
            raise CleaningError("Input text cannot be None")

        if not isinstance(text, str) or not text.strip():
            raise CleaningError("Input text cannot be empty")

        try:
            # Lowercase
            cleaned = text.lower()
            # Remove punctuation
            cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
            # Normalize whitespace
            cleaned = re.sub(r"\s+", " ", cleaned).strip()

            logger.info("Text cleaned successfully", extra={"cleaned_text": cleaned})
            return cleaned
        except Exception as exc:
            raise CleaningError("Failed to clean text") from exc


class SentimentAnalyzer:
    """Simulates sentiment analysis on cleaned text."""

    POSITIVE_WORDS = {"good", "excellent"}
    NEGATIVE_WORDS = {"bad", "terrible"}

    def process(self, text: str) -> Dict[str, Any]:
        if text is None:
            raise AnalysisError("Input text cannot be None")

        if not isinstance(text, str) or not text.strip():
            raise AnalysisError("Input text cannot be empty")

        try:
            words = set(text.split())

            score = 0
            if words & self.POSITIVE_WORDS:
                score += 1
            if words & self.NEGATIVE_WORDS:
                score -= 1

            if score > 0:
                sentiment = "positive"
            elif score < 0:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            result = {
                "text": text,
                "sentiment": sentiment,
                "score": score,
            }

            logger.info("Sentiment analyzed", extra=result)
            return result
        except Exception as exc:
            raise AnalysisError("Failed to analyze sentiment") from exc


class DatabaseStorer:
    """Stores processed data into a database."""

    def __init__(self, connection):
        self.connection = connection

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data is None or not isinstance(data, dict):
            raise StorageError("Invalid data for storage")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO sentiment_results (text, sentiment, score)"
                    "VALUES (%s, %s, %s)",
                    (data.get("text"), data.get("sentiment"), data.get("score")),
                )
            self.connection.commit()

            logger.info("Data stored successfully", extra=data)
            return data
        except Exception as exc:
            raise StorageError("Failed to store data") from exc
