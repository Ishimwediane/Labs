from src.models.user import User


def test_user_to_dict():
    """Test converting a User object to a dictionary."""
    user = User(user_id=1, name="John Doe", email="john.doe@example.com")
    assert user.to_dict() == {
        "user_id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
    }


def test_user_from_dict():
    """Test creating a User object from a dictionary."""
    user_data = {
        "user_id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
    }
    user = User.from_dict(user_data)
    assert user.user_id == 1
    assert user.name == "John Doe"
    assert user.email == "john.doe@example.com"


def test_user_creation():
    """Test creating a User object."""
    user = User(user_id=2, name="Jane Doe", email="jane.doe@example.com")
    assert user.user_id == 2
    assert user.name == "Jane Doe"
    assert user.email == "jane.doe@example.com"
