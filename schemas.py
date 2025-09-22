from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Tuple, Union
from datetime import datetime, date

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# --- 입력 모델 (프론트 -> 백엔드) ---
class ItineraryRequest(BaseModel):
    """프론트엔드에서 여행 코스 생성을 위해 보내는 데이터 모델"""
    travelDuration: int = Field(..., description="여행 기간 (일)")
    travelStartDate: str = Field(..., description="여행 시작일 (YYYY-MM-DD)")
    selected_places: List[str] = Field(..., description="사용자가 선택한 장소 ID 리스트")
    starting_point: Optional[str] = Field(None, description="부산 내 여행 시작점 장소 ID (선택사항)")
    # 아래 필드들은 프롬프트에 활용될 수 있으므로 포함합니다.
    preferences: Optional[Dict[str, bool]] = None
    surveyAttractions: Optional[List[str]] = None

# --- 출력 모델 (백엔드 -> 프론트) ---
class PlaceLocation(BaseModel):
    """장소의 위치 정보 모델"""
    type: str = "Point"
    coordinates: List[float]

class Place(BaseModel):
    """일정 내 개별 장소 정보 모델"""
    id: str = Field(..., alias="_id")
    name: str
    description: Optional[str] = None
    address: str
    location: PlaceLocation
    estimated_duration: int = Field(..., description="Gemini가 추천하는 예상 체류 시간 (시간 단위)")
    travel_time_from_previous: int = Field(..., description="이전 장소로부터의 예상 이동 시간 (분 단위)")

class DailySchedule(BaseModel):
    """일별 스케줄 모델"""
    day: int
    date: str
    places: List[Place]

class ItineraryResponse(BaseModel):
    """프론트엔드로 최종 반환될 여행 코스 전체 데이터 모델"""
    dailySchedule: List[DailySchedule]
    travelTips: str = Field(..., description="Gemini가 생성한 종합 여행 팁")

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

# 카페 스키마
class Cafe(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    category: str
    address: str
    description: str
    region: str
    location: GeoPoint
    rating: int
    review_count: int
    place_url: str
    image_url: Optional[str] = None
    tags: Optional[List] = None
    vector: Optional[List[float]] = None
    created_at: str
    updated_at: str
    distance: Optional[float] = None  # 기준 장소로부터의 거리 (km)
    
    class Config:
        extra = "ignore"

# 식당 스키마
class Restaurant(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    category: str
    address: str
    description: str
    region: str
    location: GeoPoint
    rating: int
    review_count: int
    place_url: str
    image_url: Optional[str] = None
    tags: Optional[List] = None
    vector: Optional[List[float]] = None
    created_at: str
    updated_at: str
    distance: Optional[float] = None  # 기준 장소로부터의 거리 (km)
    
    class Config:
        extra = "ignore"

 # 설문조사 반환형태 (새로운 구조)
class SurveyResponse(BaseModel):
    user_id: str
    category_group: str
    activity_level_idx: int = Field(..., ge=0, le=2, description="0: high, 1: medium, 2: low")
    time_period: int = Field(..., ge=0, le=2, description="0: 아침, 1: 오후, 2: 저녁")
    season: int = Field(..., ge=0, le=3, description="0: 봄, 1: 여름, 2: 가을, 3: 겨울")
    preference: int = Field(..., ge=0, le=1, description="0: 활동성 선호, 1: 시간대 선호")
    pos_item_index: int = Field(..., description="선호 아이템 인덱스")
    neg_item_index: int = Field(..., description="비선호 아이템 인덱스")

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
    id: Optional[str] = Field(default=None, alias="_id")  #
    user_id: str
    event: str
    target_id: str
    timestamp: datetime

# 설문조사 로그를 위한 새로운 스키마 (8요소 구조)
class Survey_log(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    category_group: str
    activity_level_idx: int  # 0: high, 1: medium, 2: low
    time_period: int  # 0: 아침, 1: 오후, 2: 저녁
    season: int  # 0: 봄, 1: 여름, 2: 가을, 3: 겨울
    preference: int  # 0: 활동성 선호, 1: 시간대 선호
    pos_item_index: int  # 선택한 관광지 인덱스
    neg_item_index: int  # 선택하지 않은 관광지 인덱스
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

# 코스에 장소 추가를 위한 스키마들
class AddPlaceToCourseRequest(BaseModel):
    """코스에 장소 추가 요청 모델"""
    course_id: str = Field(..., description="코스 ID")
    place_id: str = Field(..., description="추가할 장소 ID")
    day: int = Field(..., description="추가할 날짜 (1부터 시작)")
    position: int = Field(..., description="해당 날짜 내에서의 위치 (0부터 시작)")
    estimated_duration: int = Field(2, description="예상 체류 시간 (시간 단위, 기본값: 2)")
    travel_time_from_previous: int = Field(20, description="이전 장소로부터의 이동 시간 (분 단위, 기본값: 20)")

class UpdatePlaceInCourseRequest(BaseModel):
    """코스 내 장소 정보 수정 요청 모델"""
    course_id: str = Field(..., description="코스 ID")
    place_id: str = Field(..., description="수정할 장소 ID")
    day: int = Field(..., description="장소가 있는 날짜")
    position: int = Field(..., description="해당 날짜 내에서의 위치")
    estimated_duration: Optional[int] = Field(None, description="예상 체류 시간 (시간 단위)")
    travel_time_from_previous: Optional[int] = Field(None, description="이전 장소로부터의 이동 시간 (분 단위)")

class RemovePlaceFromCourseRequest(BaseModel):
    """코스에서 장소 제거 요청 모델"""
    course_id: str = Field(..., description="코스 ID")
    place_id: str = Field(..., description="제거할 장소 ID")
    day: int = Field(..., description="장소가 있는 날짜")
    position: int = Field(..., description="해당 날짜 내에서의 위치")

class CoursePlace(BaseModel):
    """코스 내 장소 정보 모델"""
    place_id: str
    estimated_duration: int
    travel_time_from_previous: int
    place_details: Optional[Place] = None

class CourseDay(BaseModel):
    """코스의 하루 일정 모델"""
    day: int
    date: str
    places: List[CoursePlace]

class CourseResponse(BaseModel):
    """코스 응답 모델"""
    course_id: str
    dailySchedule: List[CourseDay]
    travelTips: str
    created_at: datetime
    updated_at: datetime

# 추천 관련 스키마들
class RecommendedPlace(BaseModel):
    """추천 장소 모델"""
    place_id: str
    name: str
    category: str
    recommendation_score: float

class RecommendationRequest(BaseModel):
    """장소 추천 요청 모델"""
    user_id: Optional[str] = None
    user_preferences: Optional[List[SurveyResponse]] = None
    exclude_places: Optional[List[str]] = None
    category_filter: Optional[str] = None
    location_filter: Optional[str] = None
    use_ml: bool = False

class RecommendationResponse(BaseModel):
    """장소 추천 응답 모델"""
    places: List[RecommendedPlace]
    total_count: int
    message: str

class CategoryInfo(BaseModel):
    """카테고리 정보 모델"""
    name: str
    count: int

class LocationInfo(BaseModel):
    """지역 정보 모델"""
    name: str
    count: int

class CategoriesResponse(BaseModel):
    """카테고리 목록 응답 모델"""
    categories: List[CategoryInfo]

class LocationsResponse(BaseModel):
    """지역 목록 응답 모델"""
    locations: List[LocationInfo]

# 1.localserver.py와 호환되는 모델들
class SurveySelectionData(BaseModel):
    """설문조사 선택 데이터 모델 (1.localserver.py에서 가져옴)"""
    step: str
    value: str

class SurveyData(BaseModel):
    """설문조사 데이터 모델"""
    activity: Optional[str] = None
    activity_level: Optional[str] = None
    time: Optional[str] = None
    season: Optional[str] = None
    preference: Optional[str] = None

class VoteData(BaseModel):
    """투표 데이터 모델 (1.localserver.py와 완전히 동일)"""
    round_number: int  # 1-5 라운드 번호
    choice: str        # "option_a" 또는 "option_b"
    item_name: str     # 선택한 관광지 이름
    item_index: int    # 선택한 관광지 인덱스

class LoginData(BaseModel):
    """로그인 데이터 모델"""
    user_id: str

# 1.localserver.py의 /data 엔드포인트 응답 모델
class SurveyDataResponse(BaseModel):
    """설문조사 데이터 응답 모델 (1.localserver.py의 /data 엔드포인트와 동일)"""
    status: str
    message: Optional[str] = None
    base_schema: Optional[List] = None
    vote_schemas: Optional[List] = None
    total_votes: int
    raw_selections: Dict[str, Optional[str]]
    raw_votes: List[Dict]
    schema_explanation: Optional[Dict] = None
    current_selections: Optional[Dict[str, Optional[str]]] = None
    missing_fields: Optional[List[str]] = None
    error_details: Optional[Dict] = None

# 1.localserver.py의 추천 응답 모델
class RecommendationItem(BaseModel):
    """추천 아이템 모델"""
    item: Dict
    reason: str
    is_primary_category: bool
    weighted_score: Optional[float] = None

class RecommendationRound(BaseModel):
    """추천 라운드 모델"""
    round_number: int
    option_a: RecommendationItem
    option_b: RecommendationItem
    randomized: bool
    random_seed: Optional[int] = None

class RecommendationResponse(BaseModel):
    """추천 응답 모델 (1.localserver.py와 동일)"""
    status: str
    rounds: List[RecommendationRound]
    total_rounds: int
    total_places: int
    randomization_info: Optional[Dict] = None
    user_preferences: Optional[Dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

# 프론트엔드 전용 응답 모델들
class FrontendPlace(BaseModel):
    """프론트엔드 장소 모델"""
    id: str
    name: str
    placeId: Optional[str] = None
    time: str
    icon: Optional[str] = None

class FrontendDay(BaseModel):
    """프론트엔드 일별 스케줄 모델"""
    date: str
    dayName: str
    places: List[FrontendPlace]

class FrontendItineraryResponse(BaseModel):
    """프론트엔드 여행 일정 응답 모델"""
    itinerary: List[FrontendDay]

# 코스 저장 관련 모델들
class CourseItinerary(BaseModel):
    """코스 일정 모델"""
    days: List[CourseDay]

class CourseSaveRequest(BaseModel):
    """코스 저장 요청 모델"""
    user_id: str
    course_name: str
    itinerary: CourseItinerary

# ML 추천 관련 모델
class MLRecommendationRequest(BaseModel):
    """ML 추천 요청 모델"""
    user_id: Optional[str] = None
    vote_schemas: Optional[List[List]] = None
    top_k: int = 10
    exclude_items: Optional[List[int]] = None

class MLRecommendationResponse(BaseModel):
    """ML 추천 응답 모델"""
    status: str
    message: str
    user_id: Optional[str] = None
    recommendations: List[Dict]
    method: Optional[str] = None
    base_user_info: Optional[Dict] = None
    vote_summary: Optional[Dict] = None
    personalization_info: Optional[Dict] = None

