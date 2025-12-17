import pytest

from src.pipeline.stages import TextCleaner
from src.pipeline.exceptions import CleaningError


def test_text_cleaner_basic_cleanup():
    cleaner = TextCleaner()
    raw_text = "  Hello, WORLD!!  "

    cleaned = cleaner.process(raw_text)

    assert cleaned == "hello world"


def test_text_cleaner_removes_extra_whitespace():
    cleaner = TextCleaner()
    raw_text = "Hello     world   from   Python"

    cleaned = cleaner.process(raw_text)

    assert cleaned == "hello world from python"


def test_text_cleaner_empty_string_raises_error():
    cleaner = TextCleaner()

    with pytest.raises(CleaningError):
        cleaner.process("")


def test_text_cleaner_none_raises_error():
    cleaner = TextCleaner()

    with pytest.raises(CleaningError):
        cleaner.process(None)
