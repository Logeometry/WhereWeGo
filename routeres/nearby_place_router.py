# 가까운 장소 반환 라우터
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict
from schemas import Tourism, Cafe, Restaurant
from services.data_loader import load_location_data_from_db
from services.recommend_nearby_places import recommend_nearby_places, recommend_nearby_cafes, recommend_nearby_restaurants
# 최적화된 서비스 추가
from services.recommend_nearby_places_optimized import (
    recommend_nearby_places_optimized,
    recommend_nearby_cafes_optimized, 
    recommend_nearby_restaurants_optimized,
    recommend_nearby_all_optimized
)
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 티맵 API 키
TMAP_API_KEY = os.getenv("TMAP_API_KEY")

async def get_tmap_crowding_data(poi_id: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Dict:
    """티맵 실시간 혼잡도 데이터 조회"""
    try:
        if not TMAP_API_KEY:
            raise HTTPException(status_code=500, detail="TMAP API 키가 설정되지 않았습니다.")
        
        url = f"https://apis.openapi.sk.com/tmap/puzzle/pois/{poi_id}"
        
        params = {
            "appKey": TMAP_API_KEY
        }
        
        # 위경도가 제공된 경우에만 추가
        if lat is not None and lng is not None:
            params["lat"] = lat
            params["lng"] = lng
        
        headers = {
            "Accept": "application/json"
        }
        
        # 타임아웃 설정 (10초)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
        data = response.json()
        return data
        
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] HTTP 오류: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="API 호출 한도 초과. 잠시 후 다시 시도해주세요.")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"티맵 API 호출 오류: {e.response.text}")
    except Exception as e:
        print(f"[ERROR] 일반 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"티맵 혼잡도 조회 오류: {str(e)}")

@router.get("/nearby/{place_id}", response_model=List[Tourism])
async def get_nearby_places(place_id: str, max_distance: float = 5.0, include_crowding: bool = False):
    """
    기준 장소 주변의 관광지들을 반환합니다. (최적화됨)
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
        include_crowding: 혼잡도 정보 포함 여부 (기본값: False)
    
    Returns:
        List[Tourism]: 주변 관광지 목록 (거리순 정렬, 최대 10개)
    """
    # 최적화된 서비스 사용
    places = await recommend_nearby_places_optimized(place_id, max_distance)
    
    if include_crowding:
        # 각 장소에 혼잡도 정보 추가
        for place in places:
            try:
                # Tourism 스키마에는 poi_id가 없으므로 임시로 처리
                if hasattr(place, 'id') and place.id:
                    # 임시로 더미 POI ID 사용
                    dummy_poi_id = "10067845"  # 더현대서울 POI ID
                    coords = place.location.coordinates if place.location else [0, 0]
                    crowding_data = await get_tmap_crowding_data(dummy_poi_id, coords[1], coords[0])
                    place.crowding_info = crowding_data
                else:
                    place.crowding_info = {"error": "장소 ID가 없습니다"}
            except Exception as e:
                place.crowding_info = {"error": f"혼잡도 조회 실패: {str(e)}"}
    
    return places

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
    # 최적화된 서비스 사용
    cafes = await recommend_nearby_cafes_optimized(place_id, max_distance)
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
    # 최적화된 서비스 사용
    restaurants = await recommend_nearby_restaurants_optimized(place_id, max_distance)
    return [Restaurant(**restaurant) for restaurant in restaurants]

@router.get("/nearby/all/{place_id}")
async def get_nearby_all_places(place_id: str, max_distance: float = 5.0):
    """
    기준 장소 주변의 모든 장소들(관광지, 카페, 식당)을 반환합니다. (최적화됨 - 병렬처리)
    
    Args:
        place_id: 기준 장소의 content_id
        max_distance: 최대 거리 (km, 기본값: 5.0)
    
    Returns:
        dict: 주변 장소들을 카테고리별로 분류하여 반환
    """
    # 최적화된 병렬 처리 서비스 사용
    return await recommend_nearby_all_optimized(place_id, max_distance)



@router.get("/place/crowding/{place_id}")
async def get_place_crowding(place_id: str):
    """
    특정 장소의 혼잡도 정보만 조회합니다.
    
    Args:
        place_id: 장소의 content_id
    
    Returns:
        dict: 장소 정보와 혼잡도 데이터
    """
    try:
        # 장소 정보 조회
        places = await recommend_nearby_places(place_id, 0.1)  # 매우 작은 반경으로 해당 장소만 조회
        
        if not places:
            raise HTTPException(status_code=404, detail="장소를 찾을 수 없습니다")
        
        place = places[0]
        place_dict = place.dict()
        
        # 혼잡도 정보 조회
        try:
            # Tourism 스키마에는 poi_id가 없으므로 임시로 처리
            if hasattr(place, 'id') and place.id:
                # 임시로 더미 POI ID 사용
                dummy_poi_id = "10067845"  # 더현대서울 POI ID
                coords = place.location.coordinates if place.location else [0, 0]
                crowding_data = await get_tmap_crowding_data(dummy_poi_id, coords[1], coords[0])
                place_dict["crowding_info"] = crowding_data
            else:
                place_dict["crowding_info"] = {"error": "장소 ID가 없습니다"}
        except Exception as e:
            place_dict["crowding_info"] = {"error": f"혼잡도 조회 실패: {str(e)}"}
        
        return {
            "success": True,
            "message": "장소 혼잡도 조회 성공",
            "data": place_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장소 혼잡도 조회 중 오류 발생: {str(e)}")





