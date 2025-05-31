# DB 구조에 맞게 수정하고 통일 에정정 
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# GeoJSON Point class 정의
class GeoPoint(BaseModel):
    type: str = Literal["Point"]
    coordinates: List[float]


# 장소 스키마(DB 반영 완료)
class Tourism(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    category: str
    category_group: List[str]
    category_onehot: List[int]
    tags: List[int]
    description: str
    address: str
    region: str
    location: GeoPoint
    rating: float
    review_count: int
    visitor_count: int
    pretrained_vector: List[float]
    vector_full: List[float]
    vector_version: int
    created_at: datetime
    updated_at: datetime

# user_data 스키마 정의
class User_data(BaseModel):
    id: str = Field(..., alias="id")
    user_id: str
    oauth: str
    eamil: str
    created_at: datetime
    preference_vector: List[float]
    wishlist: List[str]

# user_log
class User_log(BaseModel):
    id: str = Field(..., alias="id")
    user_id: str
    event: str
    target_id: str
    timestamp: datetime


# (구)설문조사 반환형태
# class SurveyRequest(BaseModel):
#     username: str
#     travel_type: str
#     climate: str
#     budget: str
#     duration: str
#     companion: str

# 설문조사 반환형태
class SurveyResponse(BaseModel):
    usernume: str
    content_id: str
    name: str
    responses: Literal['like', 'neutral', 'dislike']

class CategoryScore(BaseModel):
    category: str
    score: int

class WishRequest(BaseModel):
    user_id : str
    place_id : str

class WishItem(BaseModel):
    place_id : str
    place_name : str

class LogData(BaseModel):
    user_id: str
    place_id: str
    timestamp: str

class RankingItem(BaseModel):
    place_id: str
    visits: int

