import csv
from models.user import User
from exceptions import InvalidCSVError

def parse_csv_to_users(filename: str):
    users = []

    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            name = row.get("name")
            age = row.get("age")
            email = row.get("email")

            # validate missing fields
            if not name or not age or not email:
                raise InvalidCSVError("Missing required field in CSV")

            # create User object
            user = User(
                name=name.strip(),
                age=int(age),
                email=email.strip()
            )

            users.append(user)

    return users
