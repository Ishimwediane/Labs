import pytest
from src.models.user import User
from src.parser import CSVParser
from src.exceptions import FileFormatError


@pytest.fixture
def valid_csv(tmp_path):
    """Create temporary valid CSV file."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "user_id,name,email\n"
        "1,John Doe,john@example.com\n"
        "2,Jane Smith,jane@example.com\n"
    )
    return str(csv_file)


@pytest.fixture
def empty_csv(tmp_path):
    """Create temporary empty CSV file."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("user_id,name,email\n")
    return str(csv_file)


@pytest.fixture
def malformed_csv(tmp_path):
    """Create temporary malformed CSV file."""
    csv_file = tmp_path / "malformed.csv"
    csv_file.write_text("user_id,name\n" "1,John Doe\n")
    return str(csv_file)


def test_parse_valid_csv(valid_csv):
    """Parse valid CSV successfully"""
    parser = CSVParser(valid_csv)
    users = parser.parse()
    assert len(users) == 2
    assert users[0] == User(user_id=1, name="John Doe", email="john@example.com")
    assert users[1] == User(user_id=2, name="Jane Smith", email="jane@example.com")


def test_parse_missing_file():
    """Handle missing file gracefully"""
    parser = CSVParser("non_existent_file.csv")
    with pytest.raises(FileNotFoundError):
        parser.parse()


def test_parse_empty_file(empty_csv):
    """Handle empty CSV"""
    parser = CSVParser(empty_csv)
    users = parser.parse()
    assert len(users) == 0


def test_parse_malformed_csv(malformed_csv):
    """Handle malformed CSV"""
    parser = CSVParser(malformed_csv)
    with pytest.raises(FileFormatError):
        parser.parse()
