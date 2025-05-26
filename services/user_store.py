import json
import os
from typing import Optional, Dict

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/users.json")


def load_users() -> list[Dict]:
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: list[Dict]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def find_user_by_id(user_id: str) -> Optional[Dict]:
    for u in load_users():
        if u.get("user_id") == user_id:
            return u
    return None


def find_user_by_email(email: str) -> Optional[Dict]:
    for u in load_users():
        if u.get("email") == email:
            return u
    return None


def find_user_by_oauth(oauth: str, oauth_id: str) -> Optional[Dict]:
    for u in load_users():
        if u.get("oauth") == oauth and u.get("oauth_id") == oauth_id:
            return u
    return None


def add_user(user: Dict) -> None:
    users = load_users()
    users.append(user)
    save_users(users)

# DB 연결 시 아래 코드를 대체하여 사용

# def find_user_by_id(user_id: str):
#     return db.users.find_one({"user_id": user_id})

# def find_user_by_email(email: str):
#     return db.users.find_one({"email": email})

# def find_user_by_oauth(oauth: str, oauth_id: str):
#     return db.users.find_one({"oauth": oauth, "oauth_id": oauth_id})

# def add_user(user: Dict):
#     return db.users.insert_one(user)
