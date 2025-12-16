import logging
from src.auth.models import User
from src.auth.exceptions import (
    UserAlreadyExistsError,
    InvalidPasswordError,
)
from src.auth.interfaces import UserRepository, PasswordHasher

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self, user_repository: UserRepository, password_hasher: PasswordHasher
    ):
        self._repo = user_repository
        self._hasher = password_hasher
        self._min_password_length = 8

    def register_user(self, username: str, email: str, password: str) -> User:
        # 1. Check if user already exists by email
        existing_user = self._repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"User with email '{email}' already exists.")

        # 2. Enforce password policy
        if len(password) < self._min_password_length:
            raise InvalidPasswordError(
                f"Password must be at least {self._min_password_length} characters."
            )

        # 3. Hash password
        password_hash = self._hasher.hash_password(password)

        # 4. Create user object (ID is auto-generated)
        user = User(username=username, email=email, password_hash=password_hash)

        # 5. Save to repository
        self._repo.add(user)

        # 6. Log registration
        logger.info("User registered", extra={"email": user.email})

        return user
