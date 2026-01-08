import logging
from typing import Any, Dict

from src.pipeline.stages import DatabaseStorer, SentimentAnalyzer, TextCleaner

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates the execution of all pipeline stages."""

    def __init__(
        self, cleaner: TextCleaner, analyzer: SentimentAnalyzer, storer: DatabaseStorer
    ):
        self.cleaner = cleaner
        self.analyzer = analyzer
        self.storer = storer

    def run(self, raw_text: str) -> Dict[str, Any]:
        logger.info("Pipeline started", extra={"raw_text": raw_text})

        # Stage 1: Clean text
        cleaned_text = self.cleaner.process(raw_text)
        logger.debug("Stage 1 complete", extra={"cleaned_text": cleaned_text})

        # Stage 2: Analyze sentiment
        sentiment_result = self.analyzer.process(cleaned_text)
        logger.debug("Stage 2 complete", extra=sentiment_result)

        # Stage 3: Store result
        stored_result = self.storer.process(sentiment_result)
        logger.debug("Stage 3 complete", extra=stored_result)

        logger.info("Pipeline finished successfully", extra=stored_result)
        return stored_result
