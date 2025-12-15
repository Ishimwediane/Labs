import pytest
import json
from src.models.user import User
from src.storage import UserRepository
from src.exceptions import DuplicateUserError, DatabaseError


@pytest.fixture
def empty_database(tmp_path):
    """Create empty JSON database."""
    db_file = tmp_path / "database.json"
    db_file.write_text("{}")
    return str(db_file)


@pytest.fixture
def filled_database(tmp_path):
    """Create a database with one user."""
    db_file = tmp_path / "database.json"
    users = {"1": {"name": "John Doe", "email": "john.doe@example.com"}}
    db_file.write_text(json.dumps(users))
    return str(db_file)


def test_add_user_success(empty_database):
    """Add new user successfully"""
    repo = UserRepository(db_path=empty_database)
    user = User(user_id=1, name="John Doe", email="john.doe@example.com")
    repo.add_user(user)

    with open(empty_database, "r") as f:
        data = json.load(f)

    assert "1" in data
    assert data["1"]["name"] == "John Doe"


def test_add_duplicate_user(filled_database):
    """Reject duplicate user_id"""
    repo = UserRepository(db_path=filled_database)
    user = User(user_id=1, name="Jane Smith", email="jane.smith@example.com")
    with pytest.raises(DuplicateUserError):
        repo.add_user(user)


def test_user_exists(filled_database):
    """Check if user ID exists."""
    repo = UserRepository(db_path=filled_database)
    assert repo.user_exists(1) is True
    assert repo.user_exists(2) is False


def test_database_error_on_read_only_db(filled_database):
    """Test for database error on read-only file."""
    import os

    os.chmod(filled_database, 0o444)  # read-only
    repo = UserRepository(db_path=filled_database)
    user = User(user_id=2, name="Jane Smith", email="jane.smith@example.com")
    with pytest.raises(DatabaseError):
        repo.add_user(user)
    os.chmod(filled_database, 0o666)  # make it writable again
