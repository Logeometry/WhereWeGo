from fastapi import APIRouter
from typing import List, Optional
from schemas import LocationData
from services.data_loader import load_data_from_json

router = APIRouter()

FILE_PATH = "data/temporary_data.json"
location_data = load_data_from_json(FILE_PATH)

@router.get("/categories", response_model=List[LocationData])
async def search_categories(keyword: Optional[str] = None):
    if keyword:
        return [
            loc for loc in location_data
            if any(keyword.lower() in c.lower() for c in loc.category)
        ]
    return location_data
