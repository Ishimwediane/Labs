import re
from .models.user import User
from .exceptions import ValidationError


class UserValidator:
    """Validates User objects."""

    def validate(self, user: User) -> bool:
        """
        Validates a User object.
        Raises a ValidationError if the user is invalid.
        """
        if not isinstance(user.user_id, int) or user.user_id <= 0:
            raise ValidationError("User ID must be a positive integer.")
        if not user.name:
            raise ValidationError("User name cannot be empty.")
        if not self.validate_email(user.email):
            raise ValidationError(f"Invalid email address: {user.email}")
        return True

    def validate_email(self, email: str) -> bool:
        """
        Validates an email address.
        """
        if not email:
            return False
        # A simple regex for email validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
