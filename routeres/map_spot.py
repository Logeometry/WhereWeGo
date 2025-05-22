# 지도 범위별로 정보 반환해주는 라우터
from fastapi import APIRouter, Query
from typing import List
from schemas import LocationData
from services.data_loader import load_location_data_from_json

router = APIRouter()

FILE_PATH = "data/tourist_spots_all.json"
location_data = load_location_data_from_json(FILE_PATH)

@router.get("/map_spots", response_model=List[LocationData])
async def get_spots_by_bounds(
    min_lat: float = Query(..., description="최소 위도"),
    max_lat: float = Query(..., description="최대 위도"),
    min_lng: float = Query(..., description="최소 경도"),
    max_lng: float = Query(..., description="최대 경도")
):
    result = [
        loc for loc in location_data
        if min_lat <= loc.lat <= max_lat and min_lng <= loc.lng <= max_lng
    ]
    return result

