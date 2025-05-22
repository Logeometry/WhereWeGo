import json, os

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/users.json")

def load_users():
    if not os.path.exists(DATA_PATH):
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def find_user_by_email(email):
    users = load_users()
    return next((u for u in users if u["email"] == email), None)

def add_user(user):
    users = load_users()
    users.append(user)
    save_users(users)
