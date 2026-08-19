fake_user_db = []

def get_user(username: str) -> dict[str, str] | None:
    for user in fake_user_db:
        if user["username"] == username:
            return user

    return None

def add_user(new_user: dict[str, str]) -> None:
    fake_user_db.append(new_user)