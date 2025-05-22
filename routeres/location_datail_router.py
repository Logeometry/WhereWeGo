from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import LocationData 
from services.data_loader import load_location_data_from_json
from services.click_log_service import save_click_log

router = APIRouter()

# 현재 임시 json 파일로 불러옴. 추후 DB로 변경
FILE_PATH = "data/tourlist_spots_all.json"
location_data = load_location_data_from_json(FILE_PATH)

# 장소 data load(장소에 대한 페이지 생성시)
@router.get("/detail0", response_model=List[LocationData])
async def location_detail(
    query: Optional[str] = None,
    user_id : Optional[str] = Query(None)
):
# login한 user에 대한 로그 저장
    if query:
        if user_id and user_id != "null" and user_id.strip() != "":
             save_click_log(user_id=user_id, item=query)

        return [
            item for item in location_data
            if query.lower() in item.name.lower() 
            or any(query.lower() in cat.lower() for cat in item.category)
        ]
    return location_data

# 간단 정보만 반환함 (로그 X)
@router.get("/simple_detail")
async def simple_location_detail(
    query: Optional[str] = None,
):
    if query:
        return [
            item for item in location_data
            if query.lower() in item.name.lower() 
            or (item.address and query.lower() in item.address.lower())   
        ]
    return location_data
