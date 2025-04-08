# DB 구조에 맞게 수정하고 통일 에정정 
from pydantic import BaseModel
from typing import List, Optional

class LocationData(BaseModel):
    content_id: str
    name: str
    address: str
    tel: Optional[str]
    image_url: Optional[str]
    map_x: Optional[float]
    map_y: Optional[float]
    area_code: Optional[int]
    sigungu_code: Optional[int]
    cat1: Optional[str]
    cat2: Optional[str]
    cat3: Optional[str]
    content_type_id: Optional[int]

class SurveyRequest(BaseModel):
    username: str
    travel_type: str
    climate: str
    budget: str
    duration: str
    companion: str
