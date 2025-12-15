import argparse
import logging
from src.parser import CSVParser
from src.validator import UserValidator
from src.storage import UserRepository
from src.exceptions import (
    FileFormatError,
    DuplicateUserError,
    ValidationError,
    DatabaseError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Resilient Data Importer CLI")
    parser.add_argument("csv_file", help="Path to the CSV file to import")
    parser.add_argument(
        "--db", default="users.json", help="Path to the JSON database file"
    )
    args = parser.parse_args()

    csv_parser = CSVParser(args.csv_file)
    validator = UserValidator()
    repository = UserRepository(args.db)

    try:
        users = csv_parser.parse()
        if not users:
            logger.warning("No users found in CSV file.")
            return

        for user in users:
            try:
                validator.validate(user)
                repository.add_user(user)
                logger.info(f"Added user {user.user_id}: {user.name} ({user.email})")
            except ValidationError as ve:
                logger.warning(f"Validation failed for user {user}: {ve}")
            except DuplicateUserError as de:
                logger.warning(f"Duplicate user skipped: {de}")
    except FileNotFoundError as fe:
        logger.error(f"CSV file not found: {fe}")
    except FileFormatError as ffe:
        logger.error(f"CSV format error: {ffe}")
    except DatabaseError as db_err:
        logger.error(f"Database error: {db_err}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
