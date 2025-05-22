# wishlist 가져오는 라우처
from fastapi import APIRouter
from services.wish_service import get_wishlist
from schemas import WishItem
import json
from pathlib import Path

WISH_FILE = Path("data/wish_data.json")

def load_data() -> dict:
    if not WISH_FILE.exists():
        return {}
    with open(WISH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_user_wishlist(user_id: str) -> list[str]:
    data = load_data()
    return data.get(user_id, [])