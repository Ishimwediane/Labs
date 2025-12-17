import pytest
from unittest.mock import MagicMock

from src.pipeline.stages import DatabaseStorer
from src.pipeline.exceptions import StorageError


def test_database_storer_successful_insert():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    storer = DatabaseStorer(connection=mock_connection)

    data = {
        "text": "hello world",
        "sentiment": "positive",
        "score": 1,
    }

    result = storer.process(data)

    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()
    assert result == data


def test_database_storer_raises_error_on_db_failure():
    mock_connection = MagicMock()
    mock_connection.cursor.side_effect = Exception("DB error")

    storer = DatabaseStorer(connection=mock_connection)

    data = {
        "text": "hello world",
        "sentiment": "neutral",
        "score": 0,
    }

    with pytest.raises(StorageError):
        storer.process(data)


def test_database_storer_invalid_input_raises_error():
    mock_connection = MagicMock()
    storer = DatabaseStorer(connection=mock_connection)

    with pytest.raises(StorageError):
        storer.process(None)
