# wishlist 가져오는 라우터
from fastapi import APIRouter, HTTPException
from services.wish_service import get_user_wishlist
from schemas import WishItem
from services.data_loader import load_location_data_from_db
from typing import List

router = APIRouter(prefix="/wishlist")

@router.get("/{user_id}")
async def get_wishlist(user_id: str):
    """
    사용자의 찜 목록을 반환합니다.
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        dict: 사용자의 찜 목록 (place_id 리스트)
    """
    try:
        wishlist = await get_user_wishlist(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "wishlist": wishlist,
            "count": len(wishlist)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"찜 목록 조회 중 오류 발생: {str(e)}")

@router.get("/detailed/{user_id}")
async def get_detailed_wishlist(user_id: str):
    """
    사용자의 찜 목록을 장소 상세 정보와 함께 반환합니다.
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        dict: 찜한 장소들의 상세 정보
    """
    try:
        wishlist = await get_user_wishlist(user_id)
        
        if not wishlist:
            return {
                "success": True,
                "user_id": user_id,
                "wishlist": [],
                "count": 0,
                "message": "찜한 장소가 없습니다."
            }
        
        # 장소 상세 정보 조회
        detailed_places = []
        places_data = await load_location_data_from_db()
        
        for place_id in wishlist:
            place = places_data.get(place_id)
            if place:
                detailed_places.append({
                    "place_id": place_id,
                    "name": place.get("name", "알 수 없음"),
                    "address": place.get("address", ""),
                    "category": place.get("category", ""),
                    "rating": place.get("rating", 0),
                    "description": place.get("description", "")
                })
        
        return {
            "success": True,
            "user_id": user_id,
            "wishlist": detailed_places,
            "count": len(detailed_places)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 찜 목록 조회 중 오류 발생: {str(e)}")