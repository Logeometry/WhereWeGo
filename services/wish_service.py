# MongoDB 기반 찜 기능 서비스
from datetime import datetime
from typing import List
from db import wish_col
from bson import ObjectId

async def toggle_wish(user_id: str, place_id: str) -> str:
    """
    찜 토글 (추가/제거)
    
    Args:
        user_id: 사용자 ID
        place_id: 장소 ID
    
    Returns:
        str: "added" 또는 "removed"
    """
    # 먼저 해당 place_id가 이미 찜되어 있는지 확인
    existing = await wish_col.find_one({
        "user_id": user_id,
        "wishlist": place_id
    })
    
    if existing:
        # 찜 제거 - MongoDB $pull 연산자 사용
        await wish_col.update_one(
            {"user_id": user_id},
            {
                "$pull": {"wishlist": place_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return "removed"
    else:
        # 찜 추가 - MongoDB $addToSet 연산자 사용 (중복 방지)
        result = await wish_col.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"wishlist": place_id},
                "$set": {
                    "updated_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True  # 문서가 없으면 새로 생성
        )
        return "added"

async def delete_wish(user_id: str, place_id: str) -> bool:
    """
    찜 삭제
    
    Args:
        user_id: 사용자 ID
        place_id: 장소 ID
    
    Returns:
        bool: 삭제 성공 여부
    """
    # MongoDB $pull 연산자로 직접 삭제
    result = await wish_col.update_one(
        {"user_id": user_id},
        {
            "$pull": {"wishlist": place_id},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    # modified_count가 1이면 삭제 성공
    return result.modified_count > 0

async def get_user_wishlist(user_id: str) -> List[str]:
    """
    사용자 찜 목록 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        List[str]: 찜한 장소 ID 리스트
    """
    user_wish = await wish_col.find_one({"user_id": user_id})
    
    if user_wish:
        return user_wish.get("wishlist", [])
    
    return []

async def is_wished(user_id: str, place_id: str) -> bool:
    """
    찜 상태 확인
    
    Args:
        user_id: 사용자 ID
        place_id: 장소 ID
    
    Returns:
        bool: 찜 여부
    """
    result = await wish_col.find_one({
        "user_id": user_id,
        "wishlist": place_id
    })
    return result is not None
