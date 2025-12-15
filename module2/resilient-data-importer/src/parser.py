import csv
from .models.user import User
from .exceptions import FileFormatError


class CSVParser:
    """Parses a CSV file of users."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> list[User]:
        """
        Parses the CSV file and returns a list of User objects.
        """
        users = []
        try:
            with open(self.file_path, "r", newline="") as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    # Handle empty file
                    return []

                if header != ["user_id", "name", "email"]:
                    raise FileFormatError("CSV file has incorrect headers.")

                for row in reader:
                    try:
                        user_id = int(row[0])
                        name = row[1]
                        email = row[2]
                        users.append(User(user_id=user_id, name=name, email=email))
                    except (ValueError, IndexError):
                        # Skip malformed rows
                        continue
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {self.file_path}")

        return users
