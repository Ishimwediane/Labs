import csv
from models.user import User


class UserManager:
    def __init__(self, filename):
        self.filename = filename
        self.users = []

    def load_users(self):
        """Load users from the CSV file and save then as User object"""
        try:
            with open(self.filename, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user = User(
                        name=row["name"], age=int(row["age"]), email=row["email"]
                    )
                    self.users.append(user)
            print(f"Loaded {len(self.users)} users from {self.filename}")
        except FileNotFoundError:
            print(f"File not found: {self.filename}")

    def save_users(self):
        """Save users to the CSV file"""
        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                fieldnames = ["name", "age", "email"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for user in self.users:
                    writer.writerow(
                        {"name": user.name, "age": user.age, "email": user.email}
                    )
                print(f"Saved {len(self.users)} users to {self.filename}")
        except Exception as e:
            print(f"Error saving users: {e}")

    def add_user(self, user: User):
        """Add a new user to the list"""
        self.users.append(user)
        print(f"Added user: {user}")

    def find_user(self, email: str):
        """Find a user by email"""
        for user in self.users:
            if user.email == email:
                return user
        return None
