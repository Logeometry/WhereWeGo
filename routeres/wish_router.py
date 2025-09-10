# 찜 기능 구현
from fastapi import APIRouter, Query
from schemas import WishRequest
from services.wish_service import toggle_wish, delete_wish, is_wished

router = APIRouter(prefix="/wish", tags=["Wish"])

@router.post("")
async def add_or_toggle_wish(data: WishRequest):
    result = await toggle_wish(data.user_id, data.place_id)
    return {"status": result}

@router.delete("")
async def remove_wish(data: WishRequest):
    success = await delete_wish(data.user_id, data.place_id)
    return {"status": "deleted" if success else "not_found"}

@router.get("/status")
async def check_wish_status(
    user_id: str = Query(...),
    place_id: str = Query(...)
):
    wished = await is_wished(user_id, place_id)
    return {"wished": wished}