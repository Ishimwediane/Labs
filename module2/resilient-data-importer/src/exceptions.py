class FileFormatError(Exception):
    """Raised when a CSV file has an invalid format."""


class DuplicateUserError(Exception):
    """Raised when a user with the same ID already exists."""


class DatabaseError(Exception):
    """Raised when a database write/read error occurs."""


class ValidationError(Exception):
    """Raised when user validation fails."""
