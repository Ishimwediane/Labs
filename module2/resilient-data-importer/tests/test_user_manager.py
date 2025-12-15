from src.models.user import User
from src.models.user_manager import UserManager


def test_add_user():
    manager = UserManager("dummy.csv")
    user = User(user_id=1, name="Alice", email="alice@test.com")
    manager.add_user(user)
    assert len(manager.users) == 1
    assert manager.users[0] == user


def test_find_user():
    manager = UserManager("dummy.csv")
    user = User(user_id=2, name="Bob", email="bob@test.com")
    manager.add_user(user)
    found = manager.find_user("bob@test.com")
    assert found == user


def test_find_user_not_found():
    manager = UserManager("dummy.csv")
    assert manager.find_user("missing@test.com") is None


def test_save_and_load_users(tmp_path):
    csv_file = tmp_path / "users.csv"
    manager = UserManager(csv_file)
    user1 = User(user_id=1, name="Alice", email="alice@test.com")
    user2 = User(user_id=2, name="Bob", email="bob@test.com")
    manager.add_user(user1)
    manager.add_user(user2)
    manager.save_users()

    # Load into a new manager to test reading
    new_manager = UserManager(csv_file)
    new_manager.load_users()

    assert len(new_manager.users) == 2
    assert new_manager.users[0] == user1
    assert new_manager.users[1] == user2
