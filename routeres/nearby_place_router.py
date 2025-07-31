# 가까운 장소 반환 라우터
from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import Tourism, Cafe, Restaurant
from services.data_loader import load_location_data_from_db
from services.recommend_nearby_places import recommend_nearby_places, recommend_nearby_cafes, recommend_nearby_restaurants

router = APIRouter()

@router.get("/nearby/{place_id}", response_model=List[Tourism])
async def get_nearby_places(place_id: str, max_distance: float = 5.0):
    """
    기준 장소 주변의 관광지들을 반환합니다.
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
    
    Returns:
        List[Tourism]: 주변 관광지 목록 (거리순 정렬, 최대 10개)
    """
    return await recommend_nearby_places(place_id, max_distance)

@router.get("/nearby/cafes/{place_id}", response_model=List[Cafe])
async def get_nearby_cafes(place_id: str, max_distance: float = 5.0):
    """
    기준 장소 주변의 카페들을 반환합니다.
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
    
    Returns:
        List[Cafe]: 주변 카페 목록 (거리순 정렬, 최대 10개)
    """
    cafes = await recommend_nearby_cafes(place_id, max_distance)
    return [Cafe(**cafe) for cafe in cafes]

@router.get("/nearby/restaurants/{place_id}", response_model=List[Restaurant])
async def get_nearby_restaurants(place_id: str, max_distance: float = 5.0):
    """
    기준 장소 주변의 식당들을 반환합니다.
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
    
    Returns:
        List[Restaurant]: 주변 식당 목록 (거리순 정렬, 최대 10개)
    """
    restaurants = await recommend_nearby_restaurants(place_id, max_distance)
    return [Restaurant(**restaurant) for restaurant in restaurants]

@router.get("/nearby/all/{place_id}")
async def get_nearby_all_places(place_id: str, max_distance: float = 5.0):
    """
    기준 장소 주변의 모든 장소들(관광지, 카페, 식당)을 반환합니다.
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
    
    Returns:
        dict: 주변 장소들을 카테고리별로 분류하여 반환
    """
    places = await recommend_nearby_places(place_id, max_distance)
    cafes = await recommend_nearby_cafes(place_id, max_distance)
    restaurants = await recommend_nearby_restaurants(place_id, max_distance)
    
    return {
        "tourist_spots": [place.dict() for place in places],
        "cafes": [Cafe(**cafe).dict() for cafe in cafes],
        "restaurants": [Restaurant(**restaurant).dict() for restaurant in restaurants]
    }





