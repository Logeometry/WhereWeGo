from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import LocationData
from services.data_loader import load_data_from_json
from services.click_log_service import save_click_log

router = APIRouter()

# 현재 임시 json 파일로 불러옴. 추후 DB로 변경
FILE_PATH = "data/tourist_spots_all.json"
location_data = load_data_from_json(FILE_PATH)

# 장소 data load
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
