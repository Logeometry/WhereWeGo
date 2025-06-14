from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Tuple, Union
from datetime import datetime, date

class PlaceVisit(BaseModel):
    place_id: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    type: Optional[str]
    travel_time: Optional[int]

class DayItinerary(BaseModel):
    date: date
    plan: List[PlaceVisit]

class MultiDayItineraryResponse(BaseModel):
    itinerary: List[DayItinerary]


class ItinerarySpot(BaseModel):
    place_id: str
    arrival_time: str
    leave_time: str
    coords: Tuple[float, float]

class DayCourse(BaseModel):
    date: str
    spots: List[ItinerarySpot]

# 장소 스키마(DB 반영 완료)
class GeoPoint(BaseModel):
    type: str
    coordinates: List[float]

class Tourism(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    category: str
    category_group: Union[str, List[str], None]
    category_onehot: Optional[List[int]]
    tags: Optional[List[int]]
    description: str
    address: str
    region: str
    location: GeoPoint
    rating: float
    review_count: int
    visitors_count: int
    pretrained_vector: Optional[List[float]]
    vector_full: Optional[List[float]]
    vector_version: int
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]

    class Config:
        extra = "ignore"

 # 설문조사 반환형태
class SurveyResponse(BaseModel):
    username: str
    content_id: str
    name: str
    responses: Literal['like', 'neutral', 'dislike']

class AutoMultiCourseInput(BaseModel):
    survey: List[SurveyResponse]  # ✅ 리스트로 변경
    origin_coords: Tuple[float, float]
    dest_coords: Tuple[float, float]
    accommodation_coords: Tuple[float, float]
    start_time: datetime
    end_time: datetime
    avg_stay: int

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

