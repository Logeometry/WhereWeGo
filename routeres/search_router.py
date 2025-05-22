from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import LocationData
from services.data_loader import load_location_data_from_json
from services.search_log_service import save_search_log

router = APIRouter()

FILE_PATH = 'data/tourlist_spots_all.json'
categories_data = load_location_data_from_json(FILE_PATH)

@router.get("/search", response_model=List[LocationData])
async def search_spots(
    query: Optional[str] = None,
    user_id: Optional[str] = Query(None)
):
    if query:
        # 로그인한 사용자만 로그 저장
        if user_id and user_id != "null" and user_id.strip() != "":
            save_search_log(user_id=user_id, keyword=query)

        return [
            item for item in categories_data
            if query.lower() in item.name.lower() 
            or any(query.lower() in (cat or "").lower() for cat in [item.cat1, item.cat2, item.cat3])
        ]
    return categories_data

