from typing import Dict, Any


class User:
    """Represents a user."""

    def __init__(self, user_id: int, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email

    def to_dict(self) -> Dict[str, Any]:
        """Convert the User object to a dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create a User object from a dictionary."""
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            email=data["email"],
        )

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return (
            self.user_id == other.user_id
            and self.name == other.name
            and self.email == other.email
        )
