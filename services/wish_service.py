# toggle, delete, get service 구현
import json
from pathlib import Path
from schemas import WishRequest

DATA_DIR = Path("data")
WISH_FILE = DATA_DIR / "wish_data.json"

def load_data() -> dict:
    if not WISH_FILE.exists():
        return {}
    with open(WISH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data: dict):
    with open(WISH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def toggle_wish(user_id: str, place_id: str) -> str:
    data = load_data()
    wishes = set(data.get(user_id, []))
    if place_id in wishes:
        wishes.remove(place_id)
        result = "removed"
    else:
        wishes.add(place_id)
        result = "added"
    data[user_id] = list(wishes)
    save_data(data)
    return result

def delete_wish(user_id: str, place_id: str) -> bool:
    data = load_data()
    wishes = set(data.get(user_id, []))
    if place_id in wishes:
        wishes.remove(place_id)
        data[user_id] = list(wishes)
        save_data(data)
        return True
    return False

def get_user_wishlist(user_id: str) -> list[str]:
    data = load_data()
    return data.get(user_id, [])

def is_wished(user_id: str, place_id: str) -> bool:
    return place_id in get_user_wishlist(user_id)
