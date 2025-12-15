import csv
from .user import User


class UserManager:
    def __init__(self, filename):
        self.filename = filename
        self.users = []

    def load_users(self):
        """Load users from the CSV file and store them as User objects."""
        try:
            with open(self.filename, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user = User(
                        user_id=int(row["user_id"]),  # convert string to int
                        name=row["name"],  # keep as string
                        email=row["email"],
                    )
                    self.users.append(user)
            print(f"Loaded {len(self.users)} users from {self.filename}")
        except FileNotFoundError:
            print(f"File not found: {self.filename}")

    def save_users(self):
        """Save users to the CSV file."""
        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["user_id", "name", "email"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for user in self.users:
                    writer.writerow(
                        {
                            "user_id": user.user_id,
                            "name": user.name,
                            "email": user.email,
                        }
                    )
            print(f"Saved {len(self.users)} users to {self.filename}")
        except Exception as e:
            print(f"Error saving users: {e}")

    def add_user(self, user: User):
        """Add a new user to the list."""
        self.users.append(user)
        print(f"Added user: {user}")

    def find_user(self, email: str):
        """Find a user by email."""
        for user in self.users:
            if user.email == email:
                return user
        return None
