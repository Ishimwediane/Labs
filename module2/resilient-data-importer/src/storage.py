import json
from .models.user import User
from .exceptions import DuplicateUserError, DatabaseError


class UserRepository:
    """Handles storage of users in a JSON file."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._load_database()

    def _load_database(self):
        try:
            with open(self.db_path, "r") as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}
        except json.JSONDecodeError:
            self.users = {}

    def _save_database(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.users, f, indent=4)
        except IOError as e:
            raise DatabaseError(f"Could not write to database: {e}")

    def add_user(self, user: User):
        """Adds a user to the database."""
        if str(user.user_id) in self.users:
            raise DuplicateUserError(f"User with ID {user.user_id} already exists.")

        self.users[str(user.user_id)] = {"name": user.name, "email": user.email}
        self._save_database()

    def user_exists(self, user_id: int) -> bool:
        """Checks if a user exists in the database."""
        return str(user_id) in self.users
