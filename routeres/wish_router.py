# 찜 기능 구현
from fastapi import APIRouter
from schemas import WishRequest
from services.wish_saver import save_wish
from services.wish_service import toggle_wish, delete_wish, is_wished
router = APIRouter(prefix="/wish", tags=["Wish"])

@router.post("")
def add_or_toggle_wish(data: WishRequest):
    result = toggle_wish(data.user_id, data.place_id)
    return {"status" : result}

@router.delete("")
def remove_wish(data: WishRequest):
    delete_wish(data.user_id, data.place_id)
    return {"status" : "deleted"}

@router.get("/status")
def check_wish_status(
    user_id: str = Query(...),
    place_id: str = Query(...)
):
    wished = is_wished(user_id, place_id)
    return {"wished": wished}