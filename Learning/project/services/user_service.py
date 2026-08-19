# from utils.password import hash_password

fake_user_db = []

# fake_user_db.append({
#     "username": "bob",
#     "password_hash": hash_password(password="bob123"),
#     "role": "admin"
# })

def get_user(username: str) -> dict[str, str] | None:
    for user in fake_user_db:
        if user["username"] == username:
            return user

    return None

def add_user(new_user: dict[str, str]) -> None:
    fake_user_db.append(new_user)