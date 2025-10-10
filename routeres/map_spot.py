# 지도 범위별로 정보 반환해주는 라우터
"""
현재는 사용하지 않는 라우터, 추후 삭제 예정
"""
from fastapi import APIRouter, Query
from typing import List
from schemas import Tourism
from services.data_loader import load_location_data_from_db

router = APIRouter()

@router.get("/map_spots", response_model=List[Tourism])
async def get_spots_by_bounds(
    min_lat: float = Query(..., description="최소 위도"),
    max_lat: float = Query(..., description="최대 위도"),
    min_lng: float = Query(..., description="최소 경도"),
    max_lng: float = Query(..., description="최대 경도")
):
    # MongoDB에서 모든 장소 데이터를 가져옴
    location_data = await load_location_data_from_db()
    
    result = []
    for loc in location_data:
        if hasattr(loc, 'location') and loc.location and len(loc.location.coordinates) >= 2:
            lng, lat = loc.location.coordinates[0], loc.location.coordinates[1]  # MongoDB는 [경도, 위도] 순서
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                result.append(loc)
    return result

