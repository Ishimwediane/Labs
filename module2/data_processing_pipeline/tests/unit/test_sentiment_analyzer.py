import pytest

from src.pipeline.stages import SentimentAnalyzer
from src.pipeline.exceptions import AnalysisError


def test_sentiment_analyzer_positive_text():
    analyzer = SentimentAnalyzer()
    text = "this is a good and excellent day"

    result = analyzer.process(text)

    assert result["sentiment"] == "positive"
    assert result["score"] > 0
    assert result["text"] == text


def test_sentiment_analyzer_negative_text():
    analyzer = SentimentAnalyzer()
    text = "this is a bad and terrible day"

    result = analyzer.process(text)

    assert result["sentiment"] == "negative"
    assert result["score"] < 0
    assert result["text"] == text


def test_sentiment_analyzer_neutral_text():
    analyzer = SentimentAnalyzer()
    text = "this is a day"

    result = analyzer.process(text)

    assert result["sentiment"] == "neutral"
    assert result["score"] == 0


def test_sentiment_analyzer_empty_text_raises_error():
    analyzer = SentimentAnalyzer()

    with pytest.raises(AnalysisError):
        analyzer.process("")


def test_sentiment_analyzer_none_raises_error():
    analyzer = SentimentAnalyzer()

    with pytest.raises(AnalysisError):
        analyzer.process(None)
