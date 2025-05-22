# 가까운 장소 반환 라우터
from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import LocationData
from services.data_loader import load_location_data_from_json
from services.recommend_nearby_places import recommend_nearby_places

router = APIRouter()

FILE_PATH = "data/tourlist_spots_all.json"
location_data = load_location_data_from_json(FILE_PATH)

@router.get("/nearby/{place_id}")
async def get_nearby_places(place_id: str, max_distance: float = 5.0):
    #  5.0km 이내의 장소 추천
     return await recommend_nearby_places(place_id, max_distance)
