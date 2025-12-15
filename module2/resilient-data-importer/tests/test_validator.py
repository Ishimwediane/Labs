import pytest
from src.models.user import User
from src.validator import UserValidator
from src.exceptions import ValidationError


@pytest.fixture
def validator():
    """Returns a UserValidator instance."""
    return UserValidator()


def test_validate_valid_user(validator):
    """Test validation of a valid user."""
    user = User(user_id=1, name="John Doe", email="john.doe@example.com")
    assert validator.validate(user) is True


def test_validate_invalid_email(validator):
    """Test validation of a user with an invalid email."""
    user = User(user_id=1, name="John Doe", email="john.doe")
    with pytest.raises(ValidationError):
        validator.validate(user)


def test_validate_empty_name(validator):
    """Test validation of a user with an empty name."""
    user = User(user_id=1, name="", email="john.doe@example.com")
    with pytest.raises(ValidationError):
        validator.validate(user)


def test_validate_invalid_user_id(validator):
    """Test validation of a user with an invalid user_id."""
    user = User(user_id=-1, name="John Doe", email="john.doe@example.com")
    with pytest.raises(ValidationError):
        validator.validate(user)


def test_validate_email_helper_valid(validator):
    """Test the email validation helper with a valid email."""
    assert validator.validate_email("test@example.com") is True


def test_validate_email_helper_invalid(validator):
    """Test the email validation helper with an invalid email."""
    assert validator.validate_email("test@.com") is False
    assert validator.validate_email("test.com") is False
    assert validator.validate_email("test@") is False
    assert validator.validate_email("@test.com") is False
