# DB 구조에 맞게 수정하고 통일 에정 
from pydantic import BaseModel
from typing import List

class LocationData(BaseModel):
    name: str
    location: str
    description: str
    category: List[str]
    rating: float

class SurveyRequest(BaseModel):
    username: str
    travel_type: str
    climate: str
    budget: str
    duration: str
    companion: str
