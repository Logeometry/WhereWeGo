from fastapi import APIRouter, Query
from typing import List, Optional
from schemas import LocationData
from services.data_loader import load_data_from_json

router = APIRouter()

FILE_PATH = "data/tourist_spots_all.json"
location_data = load_data_from_json(FILE_PATH)

@router.get("/categories", response_model=List[LocationData])
async def search_categories(keywords: Optional[List[str]] = Query(None)):
    if not keywords:
        return location_data

    filtered = []
    for loc in location_data:
        category_values = [loc.cat1 or "", loc.cat2 or "", loc.cat3 or ""]
        if any(kw.lower() in cat.lower() for kw in keywords for cat in category_values):
            filtered.append(loc)

    return filtered
